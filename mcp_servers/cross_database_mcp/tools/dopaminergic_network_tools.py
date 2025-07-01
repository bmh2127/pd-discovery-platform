# cross_database_mcp/tools/dopaminergic_network_tools.py
import asyncio
from typing import List, Dict, Set, Tuple, Optional
from ..utils.api_client import api_client
from ..utils.gene_mappings import gene_mapper
from ..data.evidence_data import get_dopaminergic_classification

async def build_dopaminergic_reference_network(
    discovery_mode: str = "comprehensive",
    confidence_threshold: float = 0.7,
    include_indirect: bool = True,
    max_white_nodes: int = 20
) -> dict:
    """
    Build comprehensive dopaminergic reference network for systematic discovery
    
    This is the core tool for challenging the α-synuclein paradigm by systematically
    mapping the complete dopaminergic interaction network.
    """
    
    network_results = {
        "discovery_mode": discovery_mode,
        "confidence_threshold": confidence_threshold,
        "network_construction": {},
        "systematic_analysis": {},
        "paradigm_insights": {},
        "validation_summary": {}
    }
    
    # Step 1: Define core dopaminergic protein set based on discovery mode
    core_proteins = _get_dopaminergic_protein_set(discovery_mode, include_indirect)
    network_results["network_construction"]["core_proteins"] = core_proteins
    network_results["network_construction"]["total_core_proteins"] = len(core_proteins)
    
    # Step 2: Build interaction network using cross-database approach
    try:
        network_data = await _build_cross_validated_network(
            core_proteins, confidence_threshold, max_white_nodes
        )
        network_results["network_construction"]["interaction_data"] = network_data
        network_results["network_construction"]["status"] = "success"
    except Exception as e:
        network_results["network_construction"]["status"] = "failed"
        network_results["network_construction"]["error"] = str(e)
        return network_results
    
    # Step 3: Perform systematic analysis
    systematic_analysis = await _perform_systematic_network_analysis(
        network_data, core_proteins, confidence_threshold
    )
    network_results["systematic_analysis"] = systematic_analysis
    
    # Step 4: Generate paradigm-challenging insights
    paradigm_insights = _generate_paradigm_insights(
        network_data, systematic_analysis, core_proteins
    )
    network_results["paradigm_insights"] = paradigm_insights
    
    # Step 5: Cross-database validation summary
    validation_summary = _generate_validation_summary(network_data, core_proteins)
    network_results["validation_summary"] = validation_summary
    
    return network_results

def _get_dopaminergic_protein_set(discovery_mode: str, include_indirect: bool) -> List[str]:
    """Get dopaminergic protein set based on discovery mode"""
    
    # Core dopaminergic pathway proteins (verified canonical symbols)
    synthesis_proteins = ["TH", "DDC"]
    transport_proteins = ["SLC6A3", "SLC18A2"]  # DAT, VMAT2 (canonical symbols)
    receptor_proteins = ["DRD1", "DRD2", "DRD3", "DRD4", "DRD5"]
    metabolism_proteins = ["COMT", "MAOA", "MAOB"]
    
    # PD-associated proteins with dopaminergic effects (canonical symbols)
    pd_dopaminergic_proteins = ["SNCA", "PRKN", "LRRK2", "PINK1"]  # Using PRKN not PARK2
    
    # Normalize all protein identifiers to canonical symbols
    if discovery_mode == "minimal":
        proteins = synthesis_proteins + ["SLC6A3", "DRD2"]
    elif discovery_mode == "standard":
        proteins = synthesis_proteins + transport_proteins + receptor_proteins[:2] + metabolism_proteins[:1]
    elif discovery_mode == "comprehensive":
        proteins = synthesis_proteins + transport_proteins + receptor_proteins + metabolism_proteins
        if include_indirect:
            proteins.extend(pd_dopaminergic_proteins)
    elif discovery_mode == "hypothesis_free":
        base_proteins = ["TH", "SLC6A3", "DRD2"]
        if include_indirect:
            base_proteins.extend(["SNCA", "PRKN"])
        proteins = base_proteins
    else:
        raise ValueError(f"Unknown discovery mode: {discovery_mode}")
    
    # Ensure all proteins use canonical gene symbols
    canonical_proteins = []
    for protein in proteins:
        canonical_symbol = gene_mapper.get_canonical_symbol(protein)
        canonical_proteins.append(canonical_symbol)
    
    # Remove duplicates while preserving order
    seen = set()
    final_proteins = []
    for protein in canonical_proteins:
        if protein not in seen:
            seen.add(protein)
            final_proteins.append(protein)
    
    return final_proteins

async def _build_cross_validated_network(
    core_proteins: List[str], 
    confidence_threshold: float, 
    max_white_nodes: int
) -> dict:
    """Build cross-validated interaction network"""
    
    network_data = {
        "string_network": {},
        "biogrid_interactions": {},
        "cross_validated_edges": [],
        "novel_connections": [],
        "high_confidence_subnetwork": {}
    }
    
    # Get STRING network (primary source)
    string_data = await api_client.call_mcp_tool(
        "string", "get_network",
        {
            "proteins": core_proteins,
            "species": 9606,
            "confidence": int(confidence_threshold * 1000),
            "add_white_nodes": max_white_nodes
        }
    )
    
    if string_data and "network_data" in string_data:
        interactions = string_data["network_data"]
        network_data["string_network"] = {
            "interaction_count": len(interactions),
            "interactions": interactions,
            "confidence_distribution": _analyze_confidence_distribution(interactions)
        }
        
        # Extract all proteins (including white nodes)
        all_proteins = _extract_network_proteins(interactions)
        network_data["discovered_proteins"] = list(all_proteins - set(core_proteins))
    else:
        network_data["string_network"] = {"error": "STRING network retrieval failed"}
        network_data["discovered_proteins"] = []
    
    # Get BioGRID validation for cross-database confidence
    all_network_proteins = core_proteins + network_data.get("discovered_proteins", [])[:10]  # Limit for API efficiency
    
    biogrid_data = await api_client.call_mcp_tool(
        "biogrid", "search_interactions",
        {"gene_names": all_network_proteins, "organism": "9606"}
    )
    
    if biogrid_data and not biogrid_data.get("error") and "interactions" in biogrid_data:
        biogrid_interactions = biogrid_data["interactions"]
        network_data["biogrid_interactions"] = {
            "interaction_count": len(biogrid_interactions),
            "interactions": biogrid_interactions[:20]  # Limit for response size
        }
        
        # Find cross-validated edges
        cross_validated = _find_cross_validated_interactions(
            network_data["string_network"].get("interactions", []),
            biogrid_interactions
        )
        network_data["cross_validated_edges"] = cross_validated
    else:
        network_data["biogrid_interactions"] = {"error": "BioGRID validation failed"}
        network_data["cross_validated_edges"] = []
    
    return network_data

def _analyze_confidence_distribution(interactions: List[dict]) -> dict:
    """Analyze confidence score distribution in interactions"""
    
    if not interactions:
        return {"error": "No interactions to analyze"}
    
    scores = []
    for interaction in interactions:
        score = float(interaction.get("score", 0))
        scores.append(score)
    
    scores.sort(reverse=True)
    
    return {
        "total_interactions": len(scores),
        "highest_confidence": scores[0] if scores else 0,
        "lowest_confidence": scores[-1] if scores else 0,
        "median_confidence": scores[len(scores)//2] if scores else 0,
        "high_confidence_count": len([s for s in scores if s > 800]),
        "medium_confidence_count": len([s for s in scores if 400 <= s <= 800]),
        "low_confidence_count": len([s for s in scores if s < 400])
    }

def _extract_network_proteins(interactions: List[dict]) -> Set[str]:
    """Extract all unique proteins from interaction list, normalizing to canonical symbols"""
    
    proteins = set()
    for interaction in interactions:
        # STRING uses preferredName_A and preferredName_B
        if "preferredName_A" in interaction:
            protein_a = interaction["preferredName_A"]
            canonical_a = gene_mapper.get_canonical_symbol(protein_a)
            proteins.add(canonical_a)
        if "preferredName_B" in interaction:
            protein_b = interaction["preferredName_B"]
            canonical_b = gene_mapper.get_canonical_symbol(protein_b)
            proteins.add(canonical_b)
    
    return proteins

def _find_cross_validated_interactions(
    string_interactions: List[dict], 
    biogrid_interactions: List[dict]
) -> List[dict]:
    """Find interactions that appear in both STRING and BioGRID, using canonical gene symbols"""
    
    # Extract STRING protein pairs (normalize to canonical symbols)
    string_pairs = set()
    for interaction in string_interactions:
        if "preferredName_A" in interaction and "preferredName_B" in interaction:
            protein_a = gene_mapper.get_canonical_symbol(interaction["preferredName_A"])
            protein_b = gene_mapper.get_canonical_symbol(interaction["preferredName_B"])
            pair = tuple(sorted([protein_a, protein_b]))
            string_pairs.add(pair)
    
    # Extract BioGRID protein pairs (normalize to canonical symbols)
    biogrid_pairs = set()
    for interaction in biogrid_interactions:
        if "OFFICIAL_SYMBOL_A" in interaction and "OFFICIAL_SYMBOL_B" in interaction:
            protein_a = gene_mapper.get_canonical_symbol(interaction["OFFICIAL_SYMBOL_A"])
            protein_b = gene_mapper.get_canonical_symbol(interaction["OFFICIAL_SYMBOL_B"])
            pair = tuple(sorted([protein_a, protein_b]))
            biogrid_pairs.add(pair)
    
    # Find convergent evidence
    cross_validated_pairs = string_pairs.intersection(biogrid_pairs)
    
    cross_validated = []
    for pair in cross_validated_pairs:
        cross_validated.append({
            "protein_a": pair[0],
            "protein_b": pair[1],
            "evidence_sources": ["STRING", "BioGRID"],
            "validation_confidence": "high",
            "canonical_symbols_used": True
        })
    
    return cross_validated

async def _perform_systematic_network_analysis(
    network_data: dict, 
    core_proteins: List[str], 
    confidence_threshold: float
) -> dict:
    """Perform systematic analysis of the dopaminergic network"""
    
    analysis = {
        "network_topology": {},
        "functional_clusters": {},
        "unexpected_connections": {},
        "pathway_completeness": {},
        "discovery_insights": {}
    }
    
    string_interactions = network_data.get("string_network", {}).get("interactions", [])
    
    if not string_interactions:
        analysis["error"] = "No STRING interactions available for analysis"
        return analysis
    
    # Network topology analysis
    analysis["network_topology"] = _analyze_network_topology(string_interactions, core_proteins)
    
    # Identify functional clusters
    analysis["functional_clusters"] = _identify_functional_clusters(string_interactions, core_proteins)
    
    # Find unexpected connections (paradigm-challenging)
    analysis["unexpected_connections"] = _find_unexpected_connections(
        string_interactions, core_proteins, confidence_threshold
    )
    
    # Assess pathway completeness
    analysis["pathway_completeness"] = _assess_pathway_completeness(
        string_interactions, core_proteins
    )
    
    # Generate discovery insights
    analysis["discovery_insights"] = _generate_discovery_insights(
        network_data, core_proteins, confidence_threshold
    )
    
    return analysis

def _analyze_network_topology(interactions: List[dict], core_proteins: List[str]) -> dict:
    """Analyze network topology characteristics"""
    
    # Build adjacency information
    protein_connections = {}
    for interaction in interactions:
        if "preferredName_A" in interaction and "preferredName_B" in interaction:
            protein_a = interaction["preferredName_A"]
            protein_b = interaction["preferredName_B"]
            
            if protein_a not in protein_connections:
                protein_connections[protein_a] = set()
            if protein_b not in protein_connections:
                protein_connections[protein_b] = set()
            
            protein_connections[protein_a].add(protein_b)
            protein_connections[protein_b].add(protein_a)
    
    # Calculate basic network statistics
    topology = {
        "total_proteins": len(protein_connections),
        "total_interactions": len(interactions),
        "core_protein_coverage": len([p for p in core_proteins if p in protein_connections]),
        "hub_proteins": [],
        "connectivity_distribution": {}
    }
    
    # Identify hub proteins (top 20% by connectivity)
    connectivity_scores = [(protein, len(connections)) 
                          for protein, connections in protein_connections.items()]
    connectivity_scores.sort(key=lambda x: x[1], reverse=True)
    
    hub_count = max(1, len(connectivity_scores) // 5)  # Top 20%
    topology["hub_proteins"] = [
        {"protein": protein, "connections": count}
        for protein, count in connectivity_scores[:hub_count]
    ]
    
    # Connectivity distribution
    connection_counts = [count for _, count in connectivity_scores]
    if connection_counts:
        topology["connectivity_distribution"] = {
            "max_connections": max(connection_counts),
            "min_connections": min(connection_counts),
            "average_connections": sum(connection_counts) / len(connection_counts),
            "highly_connected_count": len([c for c in connection_counts if c > 10])
        }
    
    return topology

def _identify_functional_clusters(interactions: List[dict], core_proteins: List[str]) -> dict:
    """Identify functional clusters in the dopaminergic network"""
    
    clusters = {
        "synthesis_cluster": [],
        "transport_cluster": [],
        "receptor_cluster": [],
        "metabolism_cluster": [],
        "pathology_cluster": [],
        "novel_clusters": []
    }
    
    # Define functional categories based on verified classifications
    functional_categories = {
        "synthesis": ["TH", "DDC"],
        "transport": ["SLC6A3", "SLC18A2"],  # DAT, VMAT2
        "receptor": ["DRD1", "DRD2", "DRD3", "DRD4", "DRD5"],
        "metabolism": ["COMT", "MAOA", "MAOB"],
        "pathology": ["SNCA", "PRKN", "LRRK2", "PINK1"]
    }
    
    # Find interactions within each functional category
    for category, category_proteins in functional_categories.items():
        cluster_interactions = []
        for interaction in interactions:
            if ("preferredName_A" in interaction and "preferredName_B" in interaction):
                protein_a = interaction["preferredName_A"]
                protein_b = interaction["preferredName_B"]
                
                if protein_a in category_proteins and protein_b in category_proteins:
                    cluster_interactions.append({
                        "protein_a": protein_a,
                        "protein_b": protein_b,
                        "confidence": float(interaction.get("score", 0))
                    })
        
        clusters[f"{category}_cluster"] = cluster_interactions
    
    return clusters

def _find_unexpected_connections(
    interactions: List[dict], 
    core_proteins: List[str], 
    confidence_threshold: float
) -> dict:
    """Find unexpected high-confidence connections that challenge paradigms"""
    
    unexpected = {
        "high_confidence_novel": [],
        "cross_pathway_bridges": [],
        "pathology_connections": [],
        "paradigm_challenges": []
    }
    
    # Define expected vs unexpected connection patterns
    synthesis_proteins = ["TH", "DDC"]
    pathology_proteins = ["SNCA", "PRKN", "LRRK2", "PINK1"]
    receptor_proteins = ["DRD1", "DRD2", "DRD3", "DRD4", "DRD5"]
    
    high_confidence_threshold = confidence_threshold * 1000  # Use exact threshold, not higher
    
    for interaction in interactions:
        if ("preferredName_A" in interaction and "preferredName_B" in interaction):
            protein_a = interaction["preferredName_A"]
            protein_b = interaction["preferredName_B"]
            confidence = float(interaction.get("score", 0))
            
            if confidence < high_confidence_threshold:
                continue
            
            # Check for unexpected pathology-synthesis connections
            if ((protein_a in pathology_proteins and protein_b in synthesis_proteins) or
                (protein_b in pathology_proteins and protein_a in synthesis_proteins)):
                unexpected["pathology_connections"].append({
                    "protein_a": protein_a,
                    "protein_b": protein_b,
                    "confidence": confidence,
                    "paradigm_relevance": "Direct pathology-synthesis connection challenges sequential model"
                })
            
            # Check for receptor-pathology connections
            if ((protein_a in receptor_proteins and protein_b in pathology_proteins) or
                (protein_b in receptor_proteins and protein_a in pathology_proteins)):
                unexpected["cross_pathway_bridges"].append({
                    "protein_a": protein_a,
                    "protein_b": protein_b,
                    "confidence": confidence,
                    "bridge_type": "receptor_pathology"
                })
            
            # Novel connections with proteins not in core set
            if protein_a not in core_proteins or protein_b not in core_proteins:
                unexpected["high_confidence_novel"].append({
                    "protein_a": protein_a,
                    "protein_b": protein_b,
                    "confidence": confidence,
                    "novel_protein": protein_a if protein_a not in core_proteins else protein_b
                })
    
    return unexpected

def _assess_pathway_completeness(interactions: List[dict], core_proteins: List[str]) -> dict:
    """Assess completeness of dopaminergic pathway representation"""
    
    completeness = {
        "pathway_coverage": {},
        "missing_connections": [],
        "pathway_integrity": {},
        "discovery_gaps": []
    }
    
    # Expected pathway connections (literature-based)
    expected_connections = {
        ("TH", "DDC"): "synthesis_pathway",
        ("TH", "SLC6A3"): "synthesis_transport",
        ("SLC6A3", "DRD2"): "transport_receptor",
        ("DRD2", "COMT"): "receptor_metabolism",
        ("SNCA", "TH"): "pathology_synthesis"
    }
    
    # Check which expected connections are present
    found_connections = set()
    for interaction in interactions:
        if ("preferredName_A" in interaction and "preferredName_B" in interaction):
            protein_a = interaction["preferredName_A"]
            protein_b = interaction["preferredName_B"]
            pair = tuple(sorted([protein_a, protein_b]))
            found_connections.add(pair)
    
    pathway_coverage = {}
    missing_connections = []
    
    for (protein_a, protein_b), pathway_type in expected_connections.items():
        pair = tuple(sorted([protein_a, protein_b]))
        if pair in found_connections:
            if pathway_type not in pathway_coverage:
                pathway_coverage[pathway_type] = []
            pathway_coverage[pathway_type].append({"protein_a": protein_a, "protein_b": protein_b})
        else:
            missing_connections.append({
                "protein_a": protein_a,
                "protein_b": protein_b,
                "pathway_type": pathway_type,
                "discovery_opportunity": "Missing connection suggests research gap"
            })
    
    completeness["pathway_coverage"] = pathway_coverage
    completeness["missing_connections"] = missing_connections
    completeness["coverage_percentage"] = (len(pathway_coverage) / len(expected_connections)) * 100
    
    return completeness

def _generate_discovery_insights(
    network_data: dict, 
    core_proteins: List[str], 
    confidence_threshold: float
) -> dict:
    """Generate insights for systematic discovery"""
    
    insights = {
        "research_priorities": [],
        "validation_needs": [],
        "paradigm_questions": [],
        "discovery_recommendations": []
    }
    
    # Extract key network features
    string_interactions = network_data.get("string_network", {}).get("interactions", [])
    cross_validated = network_data.get("cross_validated_edges", [])
    discovered_proteins = network_data.get("discovered_proteins", [])
    
    # Research priorities based on cross-validation
    if len(cross_validated) > 0:
        insights["research_priorities"].append({
            "priority": "high",
            "target": "cross_validated_interactions",
            "count": len(cross_validated),
            "rationale": "Interactions validated across multiple databases have high research value"
        })
    
    # Validation needs for discovered proteins
    if len(discovered_proteins) > 0:
        insights["validation_needs"].append({
            "target": "novel_dopaminergic_proteins",
            "proteins": discovered_proteins[:10],  # Top 10
            "validation_type": "functional_characterization",
            "rationale": "White node proteins may represent undiscovered dopaminergic components"
        })
    
    # Paradigm-challenging questions
    pathology_proteins = ["SNCA", "PRKN", "LRRK2", "PINK1"]
    synthesis_proteins = ["TH", "DDC"]
    
    # Check for direct pathology-synthesis connections
    direct_pathology_synthesis = 0
    for interaction in string_interactions:
        if ("preferredName_A" in interaction and "preferredName_B" in interaction):
            protein_a = interaction["preferredName_A"]
            protein_b = interaction["preferredName_B"]
            
            if ((protein_a in pathology_proteins and protein_b in synthesis_proteins) or
                (protein_b in pathology_proteins and protein_a in synthesis_proteins)):
                direct_pathology_synthesis += 1
    
    if direct_pathology_synthesis > 0:
        insights["paradigm_questions"].append({
            "question": "Do pathology proteins directly affect synthesis rather than following from it?",
            "evidence_count": direct_pathology_synthesis,
            "paradigm_challenge": "alpha_synuclein_causation",
            "research_approach": "temporal_analysis_needed"
        })
    
    # Discovery recommendations
    if len(discovered_proteins) > 5:
        insights["discovery_recommendations"].append({
            "recommendation": "systematic_characterization",
            "target": "white_node_proteins",
            "count": len(discovered_proteins),
            "approach": "functional_validation_pipeline"
        })
    
    return insights

def _generate_paradigm_insights(
    network_data: dict, 
    systematic_analysis: dict, 
    core_proteins: List[str]
) -> dict:
    """Generate insights specifically for paradigm challenging"""
    
    insights = {
        "alpha_synuclein_challenge": {},
        "temporal_disruption_hypothesis": {},
        "early_detection_targets": {},
        "therapeutic_implications": {}
    }
    
    # Analyze α-synuclein's position in the network
    string_interactions = network_data.get("string_network", {}).get("interactions", [])
    
    # Find SNCA connections and their confidence levels
    snca_connections = []
    for interaction in string_interactions:
        if ("preferredName_A" in interaction and "preferredName_B" in interaction):
            protein_a = interaction["preferredName_A"]
            protein_b = interaction["preferredName_B"]
            confidence = float(interaction.get("score", 0))
            
            if protein_a == "SNCA":
                snca_connections.append({
                    "partner": protein_b,
                    "confidence": confidence,
                    "classification": get_dopaminergic_classification(protein_b)
                })
            elif protein_b == "SNCA":
                snca_connections.append({
                    "partner": protein_a,
                    "confidence": confidence,
                    "classification": get_dopaminergic_classification(protein_a)
                })
    
    # Analyze α-synuclein paradigm challenge
    if snca_connections:
        high_conf_connections = [c for c in snca_connections if c["confidence"] > 700]
        synthesis_connections = [c for c in snca_connections if c["classification"].get("category") == "synthesis"]
        
        insights["alpha_synuclein_challenge"] = {
            "total_connections": len(snca_connections),
            "high_confidence_connections": len(high_conf_connections),
            "synthesis_connections": len(synthesis_connections),
            "paradigm_evidence": "multiple_direct_connections" if len(high_conf_connections) > 3 else "limited_direct_connections",
            "challenge_strength": "strong" if len(synthesis_connections) > 0 else "moderate"
        }
    
    # Generate temporal disruption hypothesis
    unexpected_connections = systematic_analysis.get("unexpected_connections", {})
    pathology_connections = unexpected_connections.get("pathology_connections", [])
    
    if pathology_connections:
        insights["temporal_disruption_hypothesis"] = {
            "evidence_type": "direct_pathology_synthesis_interactions",
            "connection_count": len(pathology_connections),
            "hypothesis": "Pathology proteins may disrupt synthesis before aggregation occurs",
            "research_priority": "high",
            "validation_approach": "temporal_proteomics_needed"
        }
    
    return insights

def _generate_validation_summary(network_data: dict, core_proteins: List[str]) -> dict:
    """Generate cross-database validation summary"""
    
    summary = {
        "database_coverage": {},
        "validation_confidence": {},
        "research_readiness": {},
        "next_steps": []
    }
    
    # Database coverage assessment
    string_success = "network_data" in network_data.get("string_network", {})
    biogrid_success = "interactions" in network_data.get("biogrid_interactions", {})
    
    summary["database_coverage"] = {
        "string_available": string_success,
        "biogrid_available": biogrid_success,
        "cross_validation_possible": string_success and biogrid_success,
        "coverage_score": (int(string_success) + int(biogrid_success)) / 2
    }
    
    # Validation confidence
    cross_validated_count = len(network_data.get("cross_validated_edges", []))
    total_interactions = len(network_data.get("string_network", {}).get("interactions", []))
    
    if total_interactions > 0:
        validation_rate = cross_validated_count / total_interactions
        summary["validation_confidence"] = {
            "cross_validated_interactions": cross_validated_count,
            "total_interactions": total_interactions,
            "validation_rate": validation_rate,
            "confidence_level": "high" if validation_rate > 0.3 else "moderate" if validation_rate > 0.1 else "low"
        }
    
    # Research readiness assessment
    discovered_proteins = network_data.get("discovered_proteins", [])
    summary["research_readiness"] = {
        "network_completeness": "good" if total_interactions > 20 else "limited",
        "discovery_potential": "high" if len(discovered_proteins) > 5 else "moderate",
        "paradigm_challenge_ready": cross_validated_count > 3,
        "temporal_analysis_ready": total_interactions > 10
    }
    
    return summary