# tests/test_tools_dopaminergic_network_tools.py
import pytest
from unittest.mock import AsyncMock, patch, Mock
from mcp_servers.cross_database_mcp.tools.dopaminergic_network_tools import (
    build_dopaminergic_reference_network,
    _get_dopaminergic_protein_set,
    _build_cross_validated_network,
    _analyze_confidence_distribution,
    _find_cross_validated_interactions,
    _perform_systematic_network_analysis,
    _generate_paradigm_insights
)

class TestDopaminergicNetworkTools:
    """Test suite for dopaminergic network discovery tools"""

    def test_get_dopaminergic_protein_set_minimal(self):
        """Test minimal dopaminergic protein set"""
        proteins = _get_dopaminergic_protein_set("minimal", include_indirect=False)
        
        assert "TH" in proteins  # Core synthesis
        assert "DDC" in proteins  # Core synthesis
        assert "SLC6A3" in proteins  # DAT transport
        assert "DRD2" in proteins  # Key receptor
        assert len(proteins) == 4

    def test_get_dopaminergic_protein_set_comprehensive(self):
        """Test comprehensive dopaminergic protein set"""
        proteins = _get_dopaminergic_protein_set("comprehensive", include_indirect=True)
        
        # Should include all pathway components
        assert "TH" in proteins  # Synthesis
        assert "SLC6A3" in proteins  # Transport (DAT)
        assert "SLC18A2" in proteins  # Transport (VMAT2)
        assert "DRD1" in proteins and "DRD2" in proteins  # Receptors
        assert "COMT" in proteins  # Metabolism
        assert "SNCA" in proteins  # PD-associated
        assert "PRKN" in proteins  # PD-associated (corrected)
        
        # Should be comprehensive
        assert len(proteins) >= 12

    def test_get_dopaminergic_protein_set_hypothesis_free(self):
        """Test hypothesis-free discovery mode"""
        proteins = _get_dopaminergic_protein_set("hypothesis_free", include_indirect=True)
        
        # Should start with minimal set for discovery
        assert "TH" in proteins
        assert "SLC6A3" in proteins  # DAT
        assert "DRD2" in proteins
        assert "SNCA" in proteins  # Include for paradigm challenge
        assert "PRKN" in proteins  # Include for paradigm challenge
        
        # Should be small for discovery expansion
        assert len(proteins) == 5

    def test_get_dopaminergic_protein_set_invalid_mode(self):
        """Test invalid discovery mode handling"""
        with pytest.raises(ValueError) as excinfo:
            _get_dopaminergic_protein_set("invalid_mode", include_indirect=False)
        
        assert "Unknown discovery mode" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_build_dopaminergic_reference_network_success(self):
        """Test successful dopaminergic network building"""
        # Mock STRING network response
        mock_string_response = {
            "network_data": [
                {"preferredName_A": "TH", "preferredName_B": "DDC", "score": 850},
                {"preferredName_A": "TH", "preferredName_B": "SLC6A3", "score": 780},
                {"preferredName_A": "SNCA", "preferredName_B": "TH", "score": 720},
                {"preferredName_A": "DRD2", "preferredName_B": "SLC6A3", "score": 690},
                {"preferredName_A": "COMT", "preferredName_B": "DRD2", "score": 650}
            ]
        }
        
        # Mock BioGRID response
        mock_biogrid_response = {
            "interactions": [
                {"OFFICIAL_SYMBOL_A": "TH", "OFFICIAL_SYMBOL_B": "DDC", "interaction_type": "physical"},
                {"OFFICIAL_SYMBOL_A": "SNCA", "OFFICIAL_SYMBOL_B": "TH", "interaction_type": "genetic"}
            ]
        }

        with patch('mcp_servers.cross_database_mcp.tools.dopaminergic_network_tools.api_client') as mock_api:
            mock_api.call_mcp_tool = AsyncMock(side_effect=[
                mock_string_response,  # STRING call
                mock_biogrid_response  # BioGRID call
            ])

            # Test network building
            result = await build_dopaminergic_reference_network(
                discovery_mode="comprehensive",
                confidence_threshold=0.7
            )

            # Verify result structure
            assert result["discovery_mode"] == "comprehensive"
            assert result["confidence_threshold"] == 0.7
            assert "network_construction" in result
            assert "systematic_analysis" in result
            assert "paradigm_insights" in result
            assert "validation_summary" in result

            # Verify network construction
            network_construction = result["network_construction"]
            assert network_construction["status"] == "success"
            assert "core_proteins" in network_construction
            assert "interaction_data" in network_construction

            # Verify core proteins include expected components
            core_proteins = network_construction["core_proteins"]
            assert "TH" in core_proteins
            assert "SNCA" in core_proteins  # Should include indirect
            assert "PRKN" in core_proteins  # Should include indirect (corrected)

    @pytest.mark.asyncio
    async def test_build_dopaminergic_reference_network_api_failure(self):
        """Test network building with API failure"""
        with patch('mcp_servers.cross_database_mcp.tools.dopaminergic_network_tools.api_client') as mock_api:
            mock_api.call_mcp_tool = AsyncMock(side_effect=Exception("API connection failed"))

            # Test network building with failure
            result = await build_dopaminergic_reference_network()

            # Should handle failure gracefully
            assert result["network_construction"]["status"] == "failed"
            assert "error" in result["network_construction"]

    @pytest.mark.asyncio
    async def test_build_cross_validated_network_success(self):
        """Test cross-validated network building"""
        mock_string_response = {
            "network_data": [
                {"preferredName_A": "TH", "preferredName_B": "DDC", "score": 850},
                {"preferredName_A": "SNCA", "preferredName_B": "TH", "score": 720},
                {"preferredName_A": "NOVEL_PROTEIN", "preferredName_B": "TH", "score": 680}
            ]
        }
        
        mock_biogrid_response = {
            "interactions": [
                {"OFFICIAL_SYMBOL_A": "TH", "OFFICIAL_SYMBOL_B": "DDC", "interaction_type": "physical"}
            ]
        }

        with patch('mcp_servers.cross_database_mcp.tools.dopaminergic_network_tools.api_client') as mock_api:
            mock_api.call_mcp_tool = AsyncMock(side_effect=[
                mock_string_response,
                mock_biogrid_response
            ])

            # Test cross-validated network building
            result = await _build_cross_validated_network(["TH", "SNCA"], 0.7, 10)

            # Verify STRING network data
            assert "string_network" in result
            string_network = result["string_network"]
            assert string_network["interaction_count"] == 3
            assert "confidence_distribution" in string_network

            # Verify discovered proteins (white nodes)
            assert "discovered_proteins" in result
            discovered = result["discovered_proteins"]
            assert "NOVEL_PROTEIN" in discovered

            # Verify BioGRID validation
            assert "biogrid_interactions" in result
            assert "cross_validated_edges" in result
            
            # Should find cross-validated TH-DDC interaction
            cross_validated = result["cross_validated_edges"]
            assert len(cross_validated) == 1
            assert cross_validated[0]["protein_a"] == "DDC"
            assert cross_validated[0]["protein_b"] == "TH"

    def test_analyze_confidence_distribution(self):
        """Test confidence distribution analysis"""
        interactions = [
            {"score": 900},
            {"score": 850},
            {"score": 750},
            {"score": 600},
            {"score": 450},
            {"score": 300}
        ]

        distribution = _analyze_confidence_distribution(interactions)

        assert distribution["total_interactions"] == 6
        assert distribution["highest_confidence"] == 900
        assert distribution["lowest_confidence"] == 300
        assert distribution["median_confidence"] == 600
        assert distribution["high_confidence_count"] == 2  # >800
        assert distribution["medium_confidence_count"] == 3  # 400-800
        assert distribution["low_confidence_count"] == 1  # <400

    def test_analyze_confidence_distribution_empty(self):
        """Test confidence distribution with empty interactions"""
        distribution = _analyze_confidence_distribution([])
        assert "error" in distribution

    def test_find_cross_validated_interactions(self):
        """Test finding cross-validated interactions"""
        string_interactions = [
            {"preferredName_A": "TH", "preferredName_B": "DDC", "score": 850},
            {"preferredName_A": "SNCA", "preferredName_B": "TH", "score": 720},
            {"preferredName_A": "DRD2", "preferredName_B": "SLC6A3", "score": 690}
        ]
        
        biogrid_interactions = [
            {"OFFICIAL_SYMBOL_A": "TH", "OFFICIAL_SYMBOL_B": "DDC", "interaction_type": "physical"},
            {"OFFICIAL_SYMBOL_A": "SNCA", "OFFICIAL_SYMBOL_B": "TH", "interaction_type": "genetic"},
            {"OFFICIAL_SYMBOL_A": "UNRELATED", "OFFICIAL_SYMBOL_B": "PROTEIN", "interaction_type": "physical"}
        ]

        cross_validated = _find_cross_validated_interactions(string_interactions, biogrid_interactions)

        # Should find 2 cross-validated interactions
        assert len(cross_validated) == 2
        
        # Verify cross-validated pairs
        validated_pairs = set()
        for interaction in cross_validated:
            pair = tuple(sorted([interaction["protein_a"], interaction["protein_b"]]))
            validated_pairs.add(pair)
        
        assert ("DDC", "TH") in validated_pairs
        assert ("SNCA", "TH") in validated_pairs

    @pytest.mark.asyncio
    async def test_systematic_network_analysis(self):
        """Test systematic network analysis"""
        network_data = {
            "string_network": {
                "interactions": [
                    {"preferredName_A": "TH", "preferredName_B": "DDC", "score": 850},
                    {"preferredName_A": "SNCA", "preferredName_B": "TH", "score": 720},
                    {"preferredName_A": "DRD2", "preferredName_B": "COMT", "score": 680},
                    {"preferredName_A": "NOVEL_PROTEIN", "preferredName_B": "TH", "score": 750}
                ]
            }
        }
        
        core_proteins = ["TH", "DDC", "SNCA", "DRD2", "COMT"]

        analysis = await _perform_systematic_network_analysis(
            network_data, core_proteins, 0.7
        )

        # Verify analysis structure
        assert "network_topology" in analysis
        assert "functional_clusters" in analysis
        assert "unexpected_connections" in analysis
        assert "pathway_completeness" in analysis
        assert "discovery_insights" in analysis

        # Verify network topology
        topology = analysis["network_topology"]
        assert topology["total_proteins"] > 0
        assert topology["total_interactions"] == 4
        assert "hub_proteins" in topology

        # Verify unexpected connections (SNCA-TH should be flagged)
        unexpected = analysis["unexpected_connections"]
        assert "pathology_connections" in unexpected
        
        # Should find SNCA-TH as pathology-synthesis connection
        pathology_connections = unexpected["pathology_connections"]
        assert len(pathology_connections) > 0
        
        # Check for the SNCA-TH connection specifically
        snca_th_found = any(
            (conn["protein_a"] == "SNCA" and conn["protein_b"] == "TH") or
            (conn["protein_a"] == "TH" and conn["protein_b"] == "SNCA")
            for conn in pathology_connections
        )
        assert snca_th_found

    def test_generate_paradigm_insights_alpha_synuclein_challenge(self):
        """Test paradigm insights generation for α-synuclein challenge"""
        network_data = {
            "string_network": {
                "interactions": [
                    {"preferredName_A": "SNCA", "preferredName_B": "TH", "score": 750},
                    {"preferredName_A": "SNCA", "preferredName_B": "DDC", "score": 680},
                    {"preferredName_A": "SNCA", "preferredName_B": "DRD2", "score": 620}
                ]
            }
        }
        
        systematic_analysis = {
            "unexpected_connections": {
                "pathology_connections": [
                    {"protein_a": "SNCA", "protein_b": "TH", "confidence": 750}
                ]
            }
        }

        insights = _generate_paradigm_insights(network_data, systematic_analysis, ["TH", "DDC", "SNCA"])

        # Verify α-synuclein challenge analysis
        alpha_challenge = insights["alpha_synuclein_challenge"]
        assert alpha_challenge["total_connections"] == 3
        assert alpha_challenge["high_confidence_connections"] > 0
        assert "paradigm_evidence" in alpha_challenge

        # Verify temporal disruption hypothesis
        temporal_hypothesis = insights["temporal_disruption_hypothesis"]
        assert temporal_hypothesis["evidence_type"] == "direct_pathology_synthesis_interactions"
        assert temporal_hypothesis["connection_count"] == 1
        assert temporal_hypothesis["research_priority"] == "high"

    @pytest.mark.asyncio
    async def test_dopaminergic_network_paradigm_challenge_workflow(self):
        """Test complete workflow for paradigm challenging"""
        # Mock comprehensive network with paradigm-challenging connections
        mock_string_response = {
            "network_data": [
                # Expected dopaminergic connections
                {"preferredName_A": "TH", "preferredName_B": "DDC", "score": 850},
                {"preferredName_A": "SLC6A3", "preferredName_B": "DRD2", "score": 780},
                
                # PARADIGM-CHALLENGING: Direct SNCA-synthesis connections
                {"preferredName_A": "SNCA", "preferredName_B": "TH", "score": 720},
                {"preferredName_A": "SNCA", "preferredName_B": "DDC", "score": 680},
                
                # Novel connections suggesting early disruption
                {"preferredName_A": "PRKN", "preferredName_B": "TH", "score": 650},
                {"preferredName_A": "LRRK2", "preferredName_B": "SLC6A3", "score": 630},
                
                # Discovered novel protein
                {"preferredName_A": "NOVEL_DA_PROTEIN", "preferredName_B": "TH", "score": 590}
            ]
        }
        
        mock_biogrid_response = {
            "interactions": [
                {"OFFICIAL_SYMBOL_A": "SNCA", "OFFICIAL_SYMBOL_B": "TH", "interaction_type": "physical"},
                {"OFFICIAL_SYMBOL_A": "TH", "OFFICIAL_SYMBOL_B": "DDC", "interaction_type": "physical"},
                {"OFFICIAL_SYMBOL_A": "SNCA", "OFFICIAL_SYMBOL_B": "DDC", "interaction_type": "genetic"},
                {"OFFICIAL_SYMBOL_A": "PRKN", "OFFICIAL_SYMBOL_B": "TH", "interaction_type": "physical"},
                {"OFFICIAL_SYMBOL_A": "LRRK2", "OFFICIAL_SYMBOL_B": "SLC6A3", "interaction_type": "physical"}
            ]
        }

        with patch('mcp_servers.cross_database_mcp.tools.dopaminergic_network_tools.api_client') as mock_api:
            mock_api.call_mcp_tool = AsyncMock(side_effect=[
                mock_string_response,
                mock_biogrid_response
            ])

            # Execute comprehensive paradigm-challenging analysis
            result = await build_dopaminergic_reference_network(
                discovery_mode="comprehensive",
                confidence_threshold=0.6,  # Lower threshold to capture more connections
                include_indirect=True
            )

            # Verify paradigm insights were generated
            paradigm_insights = result["paradigm_insights"]
            
            # Should challenge α-synuclein paradigm
            alpha_challenge = paradigm_insights["alpha_synuclein_challenge"]
            assert alpha_challenge["total_connections"] >= 2  # SNCA connections to TH, DDC
            assert alpha_challenge["synthesis_connections"] >= 2  # Direct synthesis connections
            assert alpha_challenge["challenge_strength"] == "strong"
            
            # Should generate temporal disruption hypothesis
            temporal_hypothesis = paradigm_insights["temporal_disruption_hypothesis"]
            assert temporal_hypothesis["evidence_type"] == "direct_pathology_synthesis_interactions"
            assert temporal_hypothesis["research_priority"] == "high"
            
            # Verify systematic analysis found unexpected connections
            systematic_analysis = result["systematic_analysis"]
            unexpected = systematic_analysis["unexpected_connections"]
            
            # Should find pathology-synthesis connections
            pathology_connections = unexpected["pathology_connections"]
            assert len(pathology_connections) >= 2  # SNCA-TH, SNCA-DDC
            
            # Should discover novel proteins
            assert "NOVEL_DA_PROTEIN" in result["network_construction"]["interaction_data"]["discovered_proteins"]
            
            # Verify validation summary indicates research readiness
            validation_summary = result["validation_summary"]
            assert validation_summary["research_readiness"]["paradigm_challenge_ready"] is True
            
            print("\n=== Paradigm Challenge Analysis Summary ===")
            print(f"α-synuclein challenge strength: {alpha_challenge['challenge_strength']}")
            print(f"Direct pathology-synthesis connections: {len(pathology_connections)}")
            print(f"Cross-validated interactions: {len(result['network_construction']['interaction_data']['cross_validated_edges'])}")
            print(f"Novel proteins discovered: {len(result['network_construction']['interaction_data']['discovered_proteins'])}")

    @pytest.mark.asyncio
    async def test_hypothesis_free_discovery_mode(self):
        """Test hypothesis-free discovery mode for unbiased network building"""
        # Mock response with unexpected connections from minimal starting set
        mock_string_response = {
            "network_data": [
                # Starting proteins
                {"preferredName_A": "TH", "preferredName_B": "SLC6A3", "score": 780},
                {"preferredName_A": "DRD2", "preferredName_B": "SLC6A3", "score": 720},
                
                # Discovered connections
                {"preferredName_A": "UNKNOWN_PROTEIN_1", "preferredName_B": "TH", "score": 650},
                {"preferredName_A": "UNKNOWN_PROTEIN_2", "preferredName_B": "DRD2", "score": 630},
                {"preferredName_A": "SNCA", "preferredName_B": "UNKNOWN_PROTEIN_1", "score": 600}
            ]
        }

        with patch('mcp_servers.cross_database_mcp.tools.dopaminergic_network_tools.api_client') as mock_api:
            mock_api.call_mcp_tool = AsyncMock(side_effect=[
                mock_string_response,
                {"interactions": []}  # Empty BioGRID for simplicity
            ])

            # Test hypothesis-free discovery
            result = await build_dopaminergic_reference_network(
                discovery_mode="hypothesis_free",
                confidence_threshold=0.6
            )

            # Should start with minimal core proteins
            core_proteins = result["network_construction"]["core_proteins"]
            assert len(core_proteins) == 5  # TH, SLC6A3, DRD2, SNCA, PRKN
            
            # Should discover novel proteins
            discovered_proteins = result["network_construction"]["interaction_data"]["discovered_proteins"]
            assert "UNKNOWN_PROTEIN_1" in discovered_proteins
            assert "UNKNOWN_PROTEIN_2" in discovered_proteins
            
            # Should generate discovery insights
            discovery_insights = result["systematic_analysis"]["discovery_insights"]
            validation_needs = discovery_insights["validation_needs"]
            
            # Should recommend validation of discovered proteins
            assert len(validation_needs) > 0
            novel_protein_validation = validation_needs[0]
            assert novel_protein_validation["target"] == "novel_dopaminergic_proteins"
            assert novel_protein_validation["validation_type"] == "functional_characterization"