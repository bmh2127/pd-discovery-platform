# tests/test_resources_protein_resources.py
import pytest
import json
import asyncio
from unittest.mock import AsyncMock, patch, Mock
from datetime import datetime
from mcp_servers.cross_database_mcp.resources.protein_resources import (
    protein_resolved_resource,
    _build_systematic_metadata,
    _get_verified_aliases,
    _get_pathway_associations_safe,
    _get_interaction_summary_safe,
    _get_evidence_based_pd_relevance,
    _build_research_context,
    _assess_dopaminergic_relevance,
    _determine_research_priority
)

class TestProteinResources:
    """Test suite for protein resources module"""

    @pytest.mark.asyncio
    async def test_protein_resolved_resource_cache_hit(self):
        """Test protein resource returns cached data when available"""
        cached_data = {
            "query": "SNCA",
            "status": "resolved",
            "cached": True
        }

        with patch('mcp_servers.cross_database_mcp.resources.protein_resources.protein_cache') as mock_cache:
            mock_cache.get.return_value = cached_data

            result = await protein_resolved_resource("SNCA")
            
            # Should return cached data as JSON
            result_data = json.loads(result)
            assert result_data["query"] == "SNCA"
            assert result_data["cached"] is True
            
            # Should not call helper function when cache hit
            mock_cache.get.assert_called_once_with("SNCA")

    @pytest.mark.asyncio
    async def test_protein_resolved_resource_cache_miss(self):
        """Test protein resource with cache miss"""
        mock_resolution_data = {
            "query": "SNCA",
            "status": "resolved",
            "overall_confidence": 0.95
        }

        with patch('mcp_servers.cross_database_mcp.resources.protein_resources.protein_cache') as mock_cache, \
             patch('mcp_servers.cross_database_mcp.tools.cross_validation_tools._resolve_protein_helper') as mock_helper:
            
            mock_cache.get.return_value = None  # Cache miss
            mock_helper.return_value = mock_resolution_data
            
            # Mock the systematic metadata building
            with patch('mcp_servers.cross_database_mcp.resources.protein_resources._build_systematic_metadata') as mock_meta:
                mock_meta.return_value = {"aliases": ["SNCA"], "pathway_associations": []}

                result = await protein_resolved_resource("SNCA")
                
                # Should call helper and cache the result
                mock_helper.assert_called_once()
                mock_cache.set.assert_called_once()
                
                # Should return enhanced data
                result_data = json.loads(result)
                assert result_data["query"] == "SNCA"
                assert result_data["status"] == "resolved"
                assert "systematic_discovery" in result_data
                assert "research_context" in result_data
                assert "cache_metadata" in result_data

    @pytest.mark.asyncio
    async def test_protein_resolved_resource_timeout(self):
        """Test protein resource with timeout"""
        with patch('mcp_servers.cross_database_mcp.resources.protein_resources.protein_cache') as mock_cache, \
             patch('mcp_servers.cross_database_mcp.tools.cross_validation_tools._resolve_protein_helper') as mock_helper:
            
            mock_cache.get.return_value = None  # Cache miss
            mock_helper.side_effect = asyncio.TimeoutError()

            result = await protein_resolved_resource("SNCA")
            
            # Should return timeout error
            result_data = json.loads(result)
            assert result_data["query"] == "SNCA"
            assert result_data["status"] == "timeout"
            assert "error" in result_data

    @pytest.mark.asyncio
    async def test_build_systematic_metadata_success(self):
        """Test building systematic metadata with successful API calls"""
        mock_aliases = ["SNCA", "alpha-synuclein"]
        mock_pathways = ["Parkinson's disease pathway", "Synuclein aggregation"]
        mock_summary = {"total_interactions": 15, "high_confidence_interactions": 8}

        with patch('mcp_servers.cross_database_mcp.resources.protein_resources._get_verified_aliases') as mock_get_aliases, \
             patch('mcp_servers.cross_database_mcp.resources.protein_resources._get_pathway_associations_safe') as mock_get_pathways, \
             patch('mcp_servers.cross_database_mcp.resources.protein_resources._get_interaction_summary_safe') as mock_get_summary:
            
            mock_get_aliases.return_value = mock_aliases
            mock_get_pathways.return_value = mock_pathways
            mock_get_summary.return_value = mock_summary

            result = await _build_systematic_metadata("SNCA")

            # Verify result structure
            assert result["aliases"] == mock_aliases
            assert result["pathway_associations"] == mock_pathways
            assert result["interaction_summary"] == mock_summary
            assert "disease_relevance" in result

    @pytest.mark.asyncio
    async def test_build_systematic_metadata_with_failures(self):
        """Test building systematic metadata with some API failures"""
        mock_aliases = ["SNCA"]
        
        with patch('mcp_servers.cross_database_mcp.resources.protein_resources._get_verified_aliases') as mock_get_aliases, \
             patch('mcp_servers.cross_database_mcp.resources.protein_resources._get_pathway_associations_safe') as mock_get_pathways, \
             patch('mcp_servers.cross_database_mcp.resources.protein_resources._get_interaction_summary_safe') as mock_get_summary:
            
            mock_get_aliases.return_value = mock_aliases
            mock_get_pathways.side_effect = Exception("API failure")
            mock_get_summary.side_effect = Exception("API failure")

            result = await _build_systematic_metadata("SNCA")

            # Should handle exceptions gracefully
            assert result["aliases"] == mock_aliases
            assert result["pathway_associations"] == []  # Fallback
            assert result["interaction_summary"]["total_interactions"] == 0  # Fallback

    def test_get_verified_aliases_known_genes(self):
        """Test verified aliases for known genes"""
        # Test SNCA
        snca_aliases = _get_verified_aliases("SNCA")
        assert "SNCA" in snca_aliases
        assert "alpha-synuclein" in snca_aliases
        assert "α-synuclein" in snca_aliases
        assert "PARK1" in snca_aliases

        # Test TH
        th_aliases = _get_verified_aliases("TH")
        assert "TH" in th_aliases
        assert "tyrosine hydroxylase" in th_aliases

        # Test PRKN (corrected from PARK2)
        prkn_aliases = _get_verified_aliases("PRKN")
        assert "PRKN" in prkn_aliases
        assert "parkin" in prkn_aliases

    def test_get_verified_aliases_with_common_aliases(self):
        """Test verified aliases using common aliases as input"""
        # Test DAT -> SLC6A3
        dat_aliases = _get_verified_aliases("DAT")
        assert "DAT" in dat_aliases
        assert "SLC6A3" in dat_aliases
        assert "dopamine transporter" in dat_aliases

        # Test PARK2 -> PRKN correction
        park2_aliases = _get_verified_aliases("PARK2")
        assert "PARK2" in park2_aliases
        assert "PRKN" in park2_aliases
        assert "parkin" in park2_aliases

    def test_get_verified_aliases_unknown_gene(self):
        """Test verified aliases for unknown genes"""
        unknown_aliases = _get_verified_aliases("UNKNOWN_GENE")
        assert unknown_aliases == ["UNKNOWN_GENE"]

    @pytest.mark.asyncio
    async def test_get_pathway_associations_safe_success(self):
        """Test successful pathway associations retrieval"""
        mock_response_data = {
            "enrichment_results": [
                {"description": "Parkinson's disease"},
                {"description": "Dopamine synthesis"},
                {"description": "Neurodegeneration"}
            ]
        }

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_client.post = AsyncMock(return_value=mock_response)

            result = await _get_pathway_associations_safe("SNCA")

            # Should return pathway descriptions
            assert len(result) == 3
            assert "Parkinson's disease" in result
            assert "Dopamine synthesis" in result

    @pytest.mark.asyncio
    async def test_get_pathway_associations_safe_failure(self):
        """Test pathway associations with API failure"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
            
            mock_client.post = AsyncMock(side_effect=Exception("Connection failed"))

            result = await _get_pathway_associations_safe("SNCA")

            # Should return empty list on failure
            assert result == []

    @pytest.mark.asyncio
    async def test_get_interaction_summary_safe_success(self):
        """Test successful interaction summary retrieval"""
        mock_response_data = {
            "network_data": [
                {"protein_a": "SNCA", "protein_b": "TH", "score": 800},
                {"protein_a": "SNCA", "protein_b": "PRKN", "score": 900},
                {"protein_a": "SNCA", "protein_b": "DRD2", "score": 600}
            ]
        }

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_client.post = AsyncMock(return_value=mock_response)

            result = await _get_interaction_summary_safe("SNCA")

            # Should calculate summary correctly
            assert result["total_interactions"] == 3
            assert result["high_confidence_interactions"] == 2  # scores > 700
            assert result["summary_available"] is True

    @pytest.mark.asyncio
    async def test_get_interaction_summary_safe_failure(self):
        """Test interaction summary with API failure"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
            
            mock_client.post = AsyncMock(side_effect=Exception("Connection failed"))

            result = await _get_interaction_summary_safe("SNCA")

            # Should return default summary on failure
            assert result["total_interactions"] == 0
            assert result["high_confidence_interactions"] == 0
            assert result["summary_available"] is False

    def test_get_evidence_based_pd_relevance_tier1_genes(self):
        """Test PD relevance for Tier 1 genes"""
        # Test SNCA (Tier 1)
        snca_relevance = _get_evidence_based_pd_relevance("SNCA")
        assert snca_relevance["parkinson_relevance_score"] == 0.95
        assert snca_relevance["evidence_tier"] == 1
        assert snca_relevance["confidence"] == "literature_validated"

        # Test PRKN (Tier 1)
        prkn_relevance = _get_evidence_based_pd_relevance("PRKN")
        assert prkn_relevance["parkinson_relevance_score"] == 0.92
        assert prkn_relevance["evidence_tier"] == 1

    def test_get_evidence_based_pd_relevance_tier2_genes(self):
        """Test PD relevance for Tier 2 genes"""
        # Test TH (Tier 2)
        th_relevance = _get_evidence_based_pd_relevance("TH")
        assert th_relevance["parkinson_relevance_score"] == 0.88
        assert th_relevance["evidence_tier"] == 2

        # Test SLC6A3/DAT (Tier 2)
        slc6a3_relevance = _get_evidence_based_pd_relevance("SLC6A3")
        assert slc6a3_relevance["parkinson_relevance_score"] == 0.85
        assert slc6a3_relevance["evidence_tier"] == 2

    def test_get_evidence_based_pd_relevance_alias_handling(self):
        """Test PD relevance with gene aliases"""
        # Test PARK2 -> PRKN mapping
        park2_relevance = _get_evidence_based_pd_relevance("PARK2")
        prkn_relevance = _get_evidence_based_pd_relevance("PRKN")
        assert park2_relevance["parkinson_relevance_score"] == prkn_relevance["parkinson_relevance_score"]

        # Test DAT -> SLC6A3 mapping
        dat_relevance = _get_evidence_based_pd_relevance("DAT")
        slc6a3_relevance = _get_evidence_based_pd_relevance("SLC6A3")
        assert dat_relevance["parkinson_relevance_score"] == slc6a3_relevance["parkinson_relevance_score"]

    def test_get_evidence_based_pd_relevance_unknown_gene(self):
        """Test PD relevance for unknown genes"""
        unknown_relevance = _get_evidence_based_pd_relevance("UNKNOWN_GENE")
        assert unknown_relevance["parkinson_relevance_score"] == 0.0
        assert unknown_relevance["evidence_tier"] == 5
        assert unknown_relevance["confidence"] == "unknown"

    def test_assess_dopaminergic_relevance_direct_markers(self):
        """Test dopaminergic relevance for direct dopaminergic markers"""
        # Test TH (synthesis)
        th_assessment = _assess_dopaminergic_relevance("TH")
        assert th_assessment["is_dopaminergic"] is True
        assert th_assessment["category"] == "synthesis"
        assert th_assessment["relevance"] == 1.0
        assert th_assessment["function"] == "rate-limiting enzyme"

        # Test SLC6A3/DAT (transport)
        slc6a3_assessment = _assess_dopaminergic_relevance("SLC6A3")
        assert slc6a3_assessment["is_dopaminergic"] is True
        assert slc6a3_assessment["category"] == "transport"
        assert slc6a3_assessment["relevance"] == 0.95

        # Test DRD2 (receptor)
        drd2_assessment = _assess_dopaminergic_relevance("DRD2")
        assert drd2_assessment["is_dopaminergic"] is True
        assert drd2_assessment["category"] == "receptor_gi"
        assert drd2_assessment["relevance"] == 0.95

    def test_assess_dopaminergic_relevance_indirect_effects(self):
        """Test dopaminergic relevance for genes with indirect effects"""
        # Test SNCA (indirect effect)
        snca_assessment = _assess_dopaminergic_relevance("SNCA")
        assert snca_assessment["is_dopaminergic"] is False
        assert snca_assessment["indirect_dopaminergic_effect"] is True
        assert snca_assessment["category"] == "pathology"
        assert snca_assessment["relevance"] == 0.8

        # Test PRKN (indirect effect)
        prkn_assessment = _assess_dopaminergic_relevance("PRKN")
        assert prkn_assessment["is_dopaminergic"] is False
        assert prkn_assessment["indirect_dopaminergic_effect"] is True

    def test_assess_dopaminergic_relevance_alias_handling(self):
        """Test dopaminergic relevance with aliases"""
        # Test DAT -> SLC6A3
        dat_assessment = _assess_dopaminergic_relevance("DAT")
        slc6a3_assessment = _assess_dopaminergic_relevance("SLC6A3")
        assert dat_assessment["relevance"] == slc6a3_assessment["relevance"]

        # Test PARK2 -> PRKN
        park2_assessment = _assess_dopaminergic_relevance("PARK2")
        prkn_assessment = _assess_dopaminergic_relevance("PRKN")
        assert park2_assessment["indirect_dopaminergic_effect"] == prkn_assessment["indirect_dopaminergic_effect"]

    def test_assess_dopaminergic_relevance_unknown_gene(self):
        """Test dopaminergic relevance for unknown genes"""
        unknown_assessment = _assess_dopaminergic_relevance("UNKNOWN_GENE")
        assert unknown_assessment["is_dopaminergic"] is False
        assert unknown_assessment["indirect_dopaminergic_effect"] is False
        assert unknown_assessment["category"] == "unknown"
        assert unknown_assessment["relevance"] == 0.0

    def test_determine_research_priority(self):
        """Test research priority determination"""
        # High priority established (direct dopaminergic, high relevance)
        th_data = {"is_dopaminergic": True, "relevance": 1.0}
        assert _determine_research_priority("TH", th_data) == "high_priority_established"

        # High priority pathology (indirect effect)
        snca_data = {"is_dopaminergic": False, "indirect_dopaminergic_effect": True}
        assert _determine_research_priority("SNCA", snca_data) == "high_priority_pathology"

        # Moderate priority
        moderate_data = {"is_dopaminergic": False, "relevance": 0.75}
        assert _determine_research_priority("TEST", moderate_data) == "moderate_priority"

        # Discovery candidate
        unknown_data = {"is_dopaminergic": False, "relevance": 0.0}
        assert _determine_research_priority("UNKNOWN", unknown_data) == "discovery_candidate"

    def test_build_research_context(self):
        """Test research context building"""
        resolution_data = {
            "status": "resolved",
            "overall_confidence": 0.95
        }

        # Mock dopaminergic assessment
        with patch('mcp_servers.cross_database_mcp.resources.protein_resources._assess_dopaminergic_relevance') as mock_assess:
            mock_assess.return_value = {
                "is_dopaminergic": True,
                "relevance": 0.95
            }

            context = _build_research_context("TH", resolution_data)

            # Verify context structure
            assert "dopaminergic_relevance" in context
            assert context["systematic_discovery_ready"] is True
            assert context["cross_database_confidence"] == 0.95
            assert "research_priority" in context
            assert "clinical_note" in context 