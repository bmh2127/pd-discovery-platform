# cross_database_mcp/tools/cross_validation_tools.py
from typing import List
from ..utils.api_client import api_client

async def _resolve_protein_helper(
    identifier: str,
    target_databases: List[str] = ["string", "pride", "biogrid"]
) -> dict:
    """Internal helper for protein resolution using centralized API client"""
    
    resolution_results = {
        "query": identifier,
        "database_mappings": {},
        "confidence_scores": {},
        "status": "processing"
    }
    
    # Try STRING mapping
    if "string" in target_databases:
        string_data = await api_client.call_mcp_tool(
            "string", "map_proteins", 
            {"proteins": [identifier], "species": 9606}
        )
        if string_data and string_data.get("mapped_proteins"):
            protein_info = string_data["mapped_proteins"][0]
            resolution_results["database_mappings"]["string"] = {
                "id": protein_info.get("stringId"),
                "name": protein_info.get("preferredName"),
                "annotation": protein_info.get("annotation")
            }
            resolution_results["confidence_scores"]["string"] = 0.95
    
    # Try PRIDE dataset search
    if "pride" in target_databases:
        pride_data = await api_client.call_mcp_tool(
            "pride", "search_projects",
            {"query": identifier, "size": 5}
        )
        if pride_data and pride_data.get("projects"):
            project_count = len(pride_data["projects"])
            resolution_results["database_mappings"]["pride"] = {
                "dataset_count": project_count,
                "sample_projects": [p.get("accession") for p in pride_data["projects"][:3]]
            }
            resolution_results["confidence_scores"]["pride"] = min(0.9, 0.3 + (project_count * 0.1))
    
    # Try BioGRID interactions
    if "biogrid" in target_databases:
        biogrid_data = await api_client.call_mcp_tool(
            "biogrid", "search_interactions",
            {"gene_names": [identifier], "organism": "9606"}
        )
        if biogrid_data and not biogrid_data.get("error"):
            interaction_count = len(biogrid_data.get("interactions", []))
            resolution_results["database_mappings"]["biogrid"] = {
                "interaction_count": interaction_count,
                "sample_interactions": biogrid_data.get("interactions", [])[:3]
            }
            resolution_results["confidence_scores"]["biogrid"] = min(0.9, 0.4 + (interaction_count * 0.01))
    
    # Determine overall status
    if resolution_results["database_mappings"]:
        resolution_results["status"] = "resolved"
        if resolution_results["confidence_scores"]:
            resolution_results["overall_confidence"] = sum(resolution_results["confidence_scores"].values()) / len(resolution_results["confidence_scores"])
        else:
            resolution_results["overall_confidence"] = 0.5
    else:
        resolution_results["status"] = "not_found"
        resolution_results["overall_confidence"] = 0.0
        resolution_results["suggestion"] = "Try checking if the protein identifier is correct or available in the target databases"
    
    return resolution_results

async def _cross_validate_interactions_helper(
    proteins: List[str],
    databases: List[str] = ["string", "biogrid"],
    confidence_threshold: float = 0.4
) -> dict:
    """Internal helper for interaction validation"""
    
    validation_results = {
        "proteins": proteins,
        "databases_checked": databases,
        "confidence_threshold": confidence_threshold,
        "validated_interactions": [],
        "database_specific": {},
        "convergent_evidence": []
    }
    
    # Get STRING interactions
    if "string" in databases:
        string_data = await api_client.call_mcp_tool(
            "string", "get_network",
            {"proteins": proteins, "confidence": int(confidence_threshold * 1000)}
        )
        if string_data and "network_data" in string_data:
            interactions = string_data["network_data"]
            validation_results["database_specific"]["string"] = {
                "interaction_count": len(interactions),
                "interactions": interactions[:10]
            }
        # Note: If API call fails or returns error, we don't create entry
    
    # Get BioGRID interactions
    if "biogrid" in databases:
        biogrid_data = await api_client.call_mcp_tool(
            "biogrid", "search_interactions",
            {"gene_names": proteins, "organism": "9606"}
        )
        if biogrid_data and not biogrid_data.get("error") and "interactions" in biogrid_data:
            interactions = biogrid_data.get("interactions", [])
            validation_results["database_specific"]["biogrid"] = {
                "interaction_count": len(interactions),
                "interactions": interactions[:10]
            }
        # Note: If API call fails or returns error, we don't create entry
    
    # Calculate convergent evidence (simplified for now)
    validation_results["summary"] = {
        "total_interactions_found": sum(
            db_data.get("interaction_count", 0) 
            for db_data in validation_results["database_specific"].values()
        ),
        "convergent_evidence_count": 0,  # TODO: Implement proper convergence detection
        "validation_confidence": "moderate"
    }
    
    return validation_results