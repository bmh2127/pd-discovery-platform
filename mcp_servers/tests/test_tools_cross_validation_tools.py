# tests/test_tools_cross_validation_tools.py
import pytest
from unittest.mock import AsyncMock, patch, Mock
from mcp_servers.cross_database_mcp.tools.cross_validation_tools import (
    _resolve_protein_helper,
    _cross_validate_interactions_helper
)

class TestCrossValidationTools:
    """Test suite for cross validation tools"""

    @pytest.mark.asyncio
    async def test_resolve_protein_helper_success(self):
        """Test successful protein resolution across databases"""
        # Mock successful API responses
        string_response = {
            "mapped_proteins": [
                {
                    "stringId": "9606.ENSP00000002434",
                    "preferredName": "SNCA",
                    "annotation": "Synuclein alpha"
                }
            ]
        }
        
        pride_response = {
            "projects": [
                {"accession": "PXD015293", "title": "Parkinson's study 1"},
                {"accession": "PXD037684", "title": "Parkinson's study 2"}
            ]
        }
        
        biogrid_response = {
            "interactions": [
                {"gene_a": "SNCA", "gene_b": "TH", "interaction_type": "physical"},
                {"gene_a": "SNCA", "gene_b": "PRKN", "interaction_type": "genetic"}
            ]
        }

        with patch('mcp_servers.cross_database_mcp.tools.cross_validation_tools.api_client') as mock_api:
            # Setup mock responses
            mock_api.call_mcp_tool = AsyncMock(side_effect=[
                string_response,  # STRING call
                pride_response,   # PRIDE call
                biogrid_response  # BioGRID call
            ])

            # Test resolution
            result = await _resolve_protein_helper("SNCA", ["string", "pride", "biogrid"])

            # Verify result structure
            assert result["query"] == "SNCA"
            assert result["status"] == "resolved"
            assert "database_mappings" in result
            assert "confidence_scores" in result
            assert "overall_confidence" in result

            # Verify database mappings
            assert "string" in result["database_mappings"]
            assert result["database_mappings"]["string"]["id"] == "9606.ENSP00000002434"
            assert result["database_mappings"]["string"]["name"] == "SNCA"

            assert "pride" in result["database_mappings"]
            assert result["database_mappings"]["pride"]["dataset_count"] == 2

            assert "biogrid" in result["database_mappings"]
            assert result["database_mappings"]["biogrid"]["interaction_count"] == 2

            # Verify confidence scores
            assert result["confidence_scores"]["string"] == 0.95
            assert result["overall_confidence"] > 0

    @pytest.mark.asyncio
    async def test_resolve_protein_helper_partial_success(self):
        """Test protein resolution with some database failures"""
        # Mock mixed responses (success + failure)
        string_response = {
            "mapped_proteins": [
                {"stringId": "9606.ENSP00000002434", "preferredName": "SNCA"}
            ]
        }

        with patch('mcp_servers.cross_database_mcp.tools.cross_validation_tools.api_client') as mock_api:
            # Setup mock responses (STRING success, others fail)
            mock_api.call_mcp_tool = AsyncMock(side_effect=[
                string_response,  # STRING success
                None,            # PRIDE failure
                None             # BioGRID failure
            ])

            # Test resolution
            result = await _resolve_protein_helper("SNCA", ["string", "pride", "biogrid"])

            # Should still be resolved with partial data
            assert result["query"] == "SNCA"
            assert result["status"] == "resolved"
            assert "string" in result["database_mappings"]
            assert "pride" not in result["database_mappings"]
            assert "biogrid" not in result["database_mappings"]

    @pytest.mark.asyncio
    async def test_resolve_protein_helper_complete_failure(self):
        """Test protein resolution when all databases fail"""
        with patch('mcp_servers.cross_database_mcp.tools.cross_validation_tools.api_client') as mock_api:
            # Setup mock for all failures
            mock_api.call_mcp_tool = AsyncMock(return_value=None)

            # Test resolution
            result = await _resolve_protein_helper("UNKNOWN_PROTEIN", ["string", "pride", "biogrid"])

            # Should report not found
            assert result["query"] == "UNKNOWN_PROTEIN"
            assert result["status"] == "not_found"
            assert result["overall_confidence"] == 0.0
            assert "suggestion" in result

    @pytest.mark.asyncio
    async def test_resolve_protein_helper_string_only(self):
        """Test protein resolution with only STRING database"""
        string_response = {
            "mapped_proteins": [
                {"stringId": "9606.ENSP00000002434", "preferredName": "SNCA"}
            ]
        }

        with patch('mcp_servers.cross_database_mcp.tools.cross_validation_tools.api_client') as mock_api:
            mock_api.call_mcp_tool = AsyncMock(return_value=string_response)

            # Test resolution with only STRING
            result = await _resolve_protein_helper("SNCA", ["string"])

            # Verify result
            assert result["query"] == "SNCA"
            assert result["status"] == "resolved"
            assert len(result["database_mappings"]) == 1
            assert "string" in result["database_mappings"]
            assert result["confidence_scores"]["string"] == 0.95

    @pytest.mark.asyncio
    async def test_cross_validate_interactions_success(self):
        """Test successful interaction validation across databases"""
        string_response = {
            "network_data": [
                {"protein_a": "SNCA", "protein_b": "TH", "score": 800},
                {"protein_a": "SNCA", "protein_b": "PRKN", "score": 900}
            ]
        }
        
        biogrid_response = {
            "interactions": [
                {"gene_a": "SNCA", "gene_b": "TH", "interaction_type": "physical"},
                {"gene_a": "SNCA", "gene_b": "PRKN", "interaction_type": "genetic"},
                {"gene_a": "TH", "gene_b": "DRD2", "interaction_type": "functional"}
            ]
        }

        with patch('mcp_servers.cross_database_mcp.tools.cross_validation_tools.api_client') as mock_api:
            mock_api.call_mcp_tool = AsyncMock(side_effect=[
                string_response,   # STRING call
                biogrid_response   # BioGRID call
            ])

            # Test validation
            result = await _cross_validate_interactions_helper(
                ["SNCA", "TH"], ["string", "biogrid"], 0.4
            )

            # Verify result structure
            assert result["proteins"] == ["SNCA", "TH"]
            assert result["databases_checked"] == ["string", "biogrid"]
            assert result["confidence_threshold"] == 0.4

            # Verify database-specific results
            assert "database_specific" in result
            assert "string" in result["database_specific"]
            assert "biogrid" in result["database_specific"]

            assert result["database_specific"]["string"]["interaction_count"] == 2
            assert result["database_specific"]["biogrid"]["interaction_count"] == 3

            # Verify summary
            assert "summary" in result
            assert result["summary"]["total_interactions_found"] == 5

    @pytest.mark.asyncio
    async def test_cross_validate_interactions_with_errors(self):
        """Test interaction validation with database errors"""
        string_response = {
            "network_data": [
                {"protein_a": "SNCA", "protein_b": "TH", "score": 800}
            ]
        }

        with patch('mcp_servers.cross_database_mcp.tools.cross_validation_tools.api_client') as mock_api:
            mock_api.call_mcp_tool = AsyncMock(side_effect=[
                string_response,  # STRING success
                {"error": "Service unavailable"}  # BioGRID error
            ])

            # Test validation
            result = await _cross_validate_interactions_helper(
                ["SNCA", "TH"], ["string", "biogrid"], 0.5
            )

            # Should handle errors gracefully
            assert result["proteins"] == ["SNCA", "TH"]
            assert "string" in result["database_specific"]
            assert result["database_specific"]["string"]["interaction_count"] == 1

            # BioGRID should not be included due to error
            assert "biogrid" not in result["database_specific"]

    @pytest.mark.asyncio
    async def test_cross_validate_interactions_empty_results(self):
        """Test interaction validation with empty results"""
        empty_string_response = {"network_data": []}
        empty_biogrid_response = {"interactions": []}

        with patch('mcp_servers.cross_database_mcp.tools.cross_validation_tools.api_client') as mock_api:
            mock_api.call_mcp_tool = AsyncMock(side_effect=[
                empty_string_response,
                empty_biogrid_response
            ])

            # Test validation
            result = await _cross_validate_interactions_helper(
                ["UNKNOWN1", "UNKNOWN2"], ["string", "biogrid"]
            )

            # Should handle empty results
            assert result["summary"]["total_interactions_found"] == 0
            assert result["database_specific"]["string"]["interaction_count"] == 0
            assert result["database_specific"]["biogrid"]["interaction_count"] == 0

    @pytest.mark.asyncio
    async def test_cross_validate_interactions_confidence_filtering(self):
        """Test that confidence threshold is properly applied"""
        string_response = {
            "network_data": [
                {"protein_a": "SNCA", "protein_b": "TH", "score": 900},      # Above threshold
                {"protein_a": "SNCA", "protein_b": "DRD2", "score": 300}    # Below threshold
            ]
        }

        with patch('mcp_servers.cross_database_mcp.tools.cross_validation_tools.api_client') as mock_api:
            mock_api.call_mcp_tool = AsyncMock(return_value=string_response)

            # Test with high confidence threshold (0.8 = 800)
            result = await _cross_validate_interactions_helper(
                ["SNCA", "TH"], ["string"], 0.8
            )

            # Verify confidence threshold was passed correctly
            expected_confidence_int = int(0.8 * 1000)  # 800
            mock_api.call_mcp_tool.assert_called_with(
                "string", "get_network",
                {"proteins": ["SNCA", "TH"], "confidence": expected_confidence_int}
            )

    @pytest.mark.asyncio
    async def test_cross_validate_with_single_protein(self):
        """Test interaction validation with single protein"""
        string_response = {
            "network_data": [
                {"protein_a": "SNCA", "protein_b": "TH", "score": 850},
                {"protein_a": "SNCA", "protein_b": "PRKN", "score": 920}
            ]
        }

        with patch('mcp_servers.cross_database_mcp.tools.cross_validation_tools.api_client') as mock_api:
            mock_api.call_mcp_tool = AsyncMock(return_value=string_response)

            # Test with single protein
            result = await _cross_validate_interactions_helper(
                ["SNCA"], ["string"], 0.4
            )

            # Should work with single protein
            assert result["proteins"] == ["SNCA"]
            assert result["database_specific"]["string"]["interaction_count"] == 2

    @pytest.mark.asyncio
    async def test_resolve_protein_with_custom_species(self):
        """Test protein resolution handles species parameter correctly"""
        string_response = {
            "mapped_proteins": [
                {"stringId": "10090.ENSMUSP00000038177", "preferredName": "Snca"}
            ]
        }

        with patch('mcp_servers.cross_database_mcp.tools.cross_validation_tools.api_client') as mock_api:
            mock_api.call_mcp_tool = AsyncMock(return_value=string_response)

            # Test resolution (should use default species 9606)
            await _resolve_protein_helper("SNCA", ["string"])

            # Verify species parameter
            mock_api.call_mcp_tool.assert_called_with(
                "string", "map_proteins",
                {"proteins": ["SNCA"], "species": 9606}
            )

    @pytest.mark.asyncio
    async def test_cross_validate_api_call_format(self):
        """Test that API calls are formatted correctly"""
        mock_response = {"network_data": [], "interactions": []}

        with patch('mcp_servers.cross_database_mcp.tools.cross_validation_tools.api_client') as mock_api:
            mock_api.call_mcp_tool = AsyncMock(return_value=mock_response)

            # Test STRING API call format
            await _cross_validate_interactions_helper(
                ["SNCA", "TH"], ["string"], 0.7
            )

            # Verify STRING call format
            mock_api.call_mcp_tool.assert_called_with(
                "string", "get_network",
                {"proteins": ["SNCA", "TH"], "confidence": 700}  # 0.7 * 1000
            )

            # Test BioGRID API call format
            await _cross_validate_interactions_helper(
                ["SNCA", "TH"], ["biogrid"], 0.5
            )

            # Verify BioGRID call format
            mock_api.call_mcp_tool.assert_called_with(
                "biogrid", "search_interactions",
                {"gene_names": ["SNCA", "TH"], "organism": "9606"}
            )

    @pytest.mark.asyncio
    async def test_handle_malformed_api_responses(self):
        """Test handling of malformed API responses"""
        # Test malformed STRING response
        malformed_string = {"invalid": "response"}
        
        # Test malformed PRIDE response  
        malformed_pride = {"wrong_key": "data"}

        with patch('mcp_servers.cross_database_mcp.tools.cross_validation_tools.api_client') as mock_api:
            mock_api.call_mcp_tool = AsyncMock(side_effect=[
                malformed_string,
                malformed_pride,
                None  # BioGRID failure
            ])

            # Test resolution with malformed responses
            result = await _resolve_protein_helper("SNCA", ["string", "pride", "biogrid"])

            # Should handle malformed responses gracefully
            assert result["query"] == "SNCA"
            # May still be resolved if any database worked, or not_found if all failed
            assert result["status"] in ["resolved", "not_found"] 