# cross_database_mcp/server.py
from fastmcp import FastMCP
from pydantic import BaseModel
import httpx
import json
import os
from typing import List, Optional, Dict

mcp = FastMCP("Cross-Database Integration Server")

# Configuration for other MCP servers
STRING_MCP_URL = os.getenv("STRING_MCP_URL", "http://localhost:8001")
PRIDE_MCP_URL = os.getenv("PRIDE_MCP_URL", "http://localhost:8002")
BIOGRID_MCP_URL = os.getenv("BIOGRID_MCP_URL", "http://localhost:8003")
PPX_MCP_URL = os.getenv("PPX_MCP_URL", "http://localhost:8004")

# === HELPER FUNCTIONS (not decorated - can be called internally) ===

async def _resolve_protein_helper(
    identifier: str,
    target_databases: List[str] = ["string", "pride", "biogrid"]
) -> dict:
    """Internal helper for protein resolution"""
    
    resolution_results = {
        "query": identifier,
        "database_mappings": {},
        "confidence_scores": {},
        "aliases": [],
        "status": "processing"
    }
    
    # Try STRING mapping
    if "string" in target_databases:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{STRING_MCP_URL}/call_tool",
                    json={
                        "name": "map_proteins",
                        "arguments": {"proteins": [identifier], "species": 9606}
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("mapped_proteins") and len(data["mapped_proteins"]) > 0:
                        protein_info = data["mapped_proteins"][0]
                        resolution_results["database_mappings"]["string"] = {
                            "id": protein_info.get("stringId"),
                            "name": protein_info.get("preferredName"),
                            "annotation": protein_info.get("annotation")
                        }
                        resolution_results["confidence_scores"]["string"] = 0.95
        except Exception as e:
            resolution_results["errors"] = resolution_results.get("errors", [])
            resolution_results["errors"].append(f"STRING resolution failed: {str(e)}")
    
    # Try PRIDE dataset search
    if "pride" in target_databases:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{PRIDE_MCP_URL}/call_tool",
                    json={
                        "name": "search_projects",
                        "arguments": {"query": identifier, "size": 5}
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    project_count = len(data.get("projects", []))
                    resolution_results["database_mappings"]["pride"] = {
                        "dataset_count": project_count,
                        "sample_projects": [p.get("accession") for p in data.get("projects", [])[:3]]
                    }
                    # Higher confidence with more datasets
                    resolution_results["confidence_scores"]["pride"] = min(0.9, 0.3 + (project_count * 0.1))
        except Exception as e:
            resolution_results["errors"] = resolution_results.get("errors", [])
            resolution_results["errors"].append(f"PRIDE resolution failed: {str(e)}")
    
    # Try BioGRID interactions
    if "biogrid" in target_databases:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{BIOGRID_MCP_URL}/call_tool",
                    json={
                        "name": "search_interactions",
                        "arguments": {"genes": [identifier], "organism": "9606"}
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    interaction_count = len(data.get("interactions", []))
                    resolution_results["database_mappings"]["biogrid"] = {
                        "interaction_count": interaction_count,
                        "sample_interactions": data.get("interactions", [])[:3]
                    }
                    resolution_results["confidence_scores"]["biogrid"] = min(0.9, 0.4 + (interaction_count * 0.01))
        except Exception as e:
            resolution_results["errors"] = resolution_results.get("errors", [])
            resolution_results["errors"].append(f"BioGRID resolution failed: {str(e)}")
    
    # Determine overall status and confidence
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
    """Internal helper for interaction validation using real API calls"""
    
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
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{STRING_MCP_URL}/call_tool",
                    json={
                        "name": "get_network",
                        "arguments": {
                            "proteins": proteins,
                            "confidence": int(confidence_threshold * 1000)  # STRING uses 0-1000 scale
                        }
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    interactions = data.get("network_data", [])
                    validation_results["database_specific"]["string"] = {
                        "interaction_count": len(interactions),
                        "interactions": interactions[:10]  # Limit for response size
                    }
        except Exception as e:
            validation_results["errors"] = validation_results.get("errors", [])
            validation_results["errors"].append(f"STRING validation failed: {str(e)}")
    
    # Get BioGRID interactions
    if "biogrid" in databases:
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{BIOGRID_MCP_URL}/call_tool",
                    json={
                        "name": "search_interactions",
                        "arguments": {"genes": proteins, "organism": "9606"}
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    interactions = data.get("interactions", [])
                    validation_results["database_specific"]["biogrid"] = {
                        "interaction_count": len(interactions),
                        "interactions": interactions[:10]  # Limit for response size
                    }
        except Exception as e:
            validation_results["errors"] = validation_results.get("errors", [])
            validation_results["errors"].append(f"BioGRID validation failed: {str(e)}")
    
    # Find convergent evidence by comparing interactions between databases
    string_interactions = validation_results["database_specific"].get("string", {}).get("interactions", [])
    biogrid_interactions = validation_results["database_specific"].get("biogrid", {}).get("interactions", [])
    
    # Extract protein pairs from both databases for comparison
    string_pairs = set()
    for interaction in string_interactions:
        if "preferredName_A" in interaction and "preferredName_B" in interaction:
            pair = tuple(sorted([interaction["preferredName_A"], interaction["preferredName_B"]]))
            string_pairs.add(pair)
    
    biogrid_pairs = set()
    for interaction in biogrid_interactions:
        if "OFFICIAL_SYMBOL_A" in interaction and "OFFICIAL_SYMBOL_B" in interaction:
            pair = tuple(sorted([interaction["OFFICIAL_SYMBOL_A"], interaction["OFFICIAL_SYMBOL_B"]]))
            biogrid_pairs.add(pair)
    
    # Find overlapping interactions
    convergent_pairs = string_pairs.intersection(biogrid_pairs)
    for pair in convergent_pairs:
        validation_results["convergent_evidence"].append({
            "proteins": list(pair),
            "databases": ["string", "biogrid"],
            "evidence_type": "cross_database_validation"
        })
    
    validation_results["summary"] = {
        "total_interactions_found": sum(
            db_data.get("interaction_count", 0) 
            for db_data in validation_results["database_specific"].values()
        ),
        "convergent_evidence_count": len(validation_results["convergent_evidence"]),
        "validation_confidence": "high" if validation_results["convergent_evidence"] else "moderate"
    }
    
    return validation_results

# === RESOURCES: Unified Cross-Database Views ===

@mcp.resource("research://parkinson/overview")
async def pd_research_overview_resource():
    """Comprehensive Parkinson's disease research overview"""
    
    overview = {
        "biomarkers": {
            "established": ["SNCA", "PARK2", "TH", "DRD2"],
            "emerging": ["LRRK2", "PINK1", "COMT", "UCHL1"],
            "total_count": 8
        },
        "datasets": {
            "pride_proteomics": [],
            "string_networks": [
                "string://markers/dopaminergic"
            ],
            "total_datasets": 0
        },
        "research_workflows": [
            "workflow://pd-biomarker-discovery",
            "workflow://cross-database-validation",
            "workflow://clinical-translation"
        ],
        "key_pathways": [
            "Dopamine synthesis",
            "Mitochondrial function", 
            "Protein aggregation",
            "Neuroinflammation",
            "Autophagy/mitophagy"
        ],
        "database_coverage": {
            "STRING": "protein interactions",
            "PRIDE": "proteomics datasets",
            "BioGRID": "validated interactions",
            "PPX": "expression profiles"
        },
        "note": "For individual protein resolution, use the resolve_protein_entity tool for real-time cross-database data"
    }
    
    # Fetch real verified datasets from PRIDE MCP
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{PRIDE_MCP_URL}/read_resource",
                params={"uri": "research://parkinson/datasets/pride"}
            )
            if response.status_code == 200:
                pride_data = response.json()
                if isinstance(pride_data, list) and len(pride_data) > 0:
                    # Extract text content and parse JSON
                    content = pride_data[0].get("text", "{}")
                    try:
                        pride_datasets = json.loads(content)
                        # Extract dataset IDs from the proteomics_datasets
                        if "proteomics_datasets" in pride_datasets:
                            dataset_ids = list(pride_datasets["proteomics_datasets"].keys())
                            overview["datasets"]["pride_proteomics"] = dataset_ids
                            overview["datasets"]["total_datasets"] = len(dataset_ids)
                    except json.JSONDecodeError:
                        pass
    except Exception as e:
        # Fallback to some verified datasets if PRIDE service is unavailable
        overview["datasets"]["pride_proteomics"] = [
            "PXD015293",  # Mouse models
            "PXD037684",  # Human substantia nigra 
            "PXD047134",  # GBA1 mutation study
            "PXD030142",  # Single-cell study
            "PXD020722"   # Urinary biomarkers
        ]
        overview["datasets"]["total_datasets"] = 5
        overview["service_status"] = f"PRIDE service unavailable: {str(e)}"
    
    # Fetch dopaminergic markers from STRING MCP
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{STRING_MCP_URL}/read_resource",
                params={"uri": "string://markers/dopaminergic"}
            )
            if response.status_code == 200:
                string_data = response.json()
                if isinstance(string_data, list) and len(string_data) > 0:
                    content = string_data[0].get("text", "{}")
                    try:
                        markers_data = json.loads(content)
                        # Update biomarkers with STRING data if available
                        if "core_proteins" in markers_data:
                            overview["biomarkers"]["string_validated"] = markers_data["core_proteins"]
                    except json.JSONDecodeError:
                        pass
    except Exception as e:
        overview["service_status"] = overview.get("service_status", "") + f" STRING service: {str(e)}"
    
    return json.dumps(overview, indent=2)

@mcp.resource("workflow://pd-biomarker-discovery")
async def pd_biomarker_workflow_resource():
    """Parkinson's disease biomarker discovery workflow template"""
    
    workflow = {
        "name": "PD Biomarker Discovery Workflow",
        "description": "Systematic approach to identify and validate PD biomarkers using real-time cross-database integration",
        "steps": [
            {
                "step": 1,
                "name": "Get research overview",
                "resources": ["research://parkinson/overview"],
                "description": "Review established and emerging biomarkers, available datasets"
            },
            {
                "step": 2,
                "name": "Resolve target proteins",
                "tools": ["resolve_protein_entity"],
                "description": "Get real-time cross-database mappings and confidence scores",
                "output": "unified protein mappings with confidence"
            },
            {
                "step": 3,
                "name": "Cross-validate interactions",
                "tools": ["cross_validate_interactions"],
                "description": "Find convergent evidence across STRING and BioGRID",
                "output": "interaction network with validation confidence"
            },
            {
                "step": 4,
                "name": "Execute comprehensive workflow",
                "tools": ["execute_pd_workflow"],
                "description": "Run complete analysis pipeline",
                "output": "validated biomarker candidates with recommendations"
            },
            {
                "step": 5,
                "name": "Get additional candidates",
                "tools": ["get_biomarker_candidates"],
                "description": "Retrieve curated biomarker sets",
                "output": "ranked candidate list"
            }
        ],
        "expected_duration": "5-15 minutes (real-time API calls)",
        "output_format": "comprehensive research report",
        "confidence_thresholds": {
            "minimum_databases": 2,
            "minimum_confidence": 0.7,
            "minimum_interactions": 5
        },
        "advantages": [
            "Real-time data from multiple databases",
            "Cross-database validation and confidence scoring", 
            "Convergent evidence identification",
            "Graceful handling of service unavailability"
        ]
    }
    
    return json.dumps(workflow, indent=2)

# === TOOLS: Cross-Database Operations ===

@mcp.tool()
async def resolve_protein_entity(
    identifier: str,
    target_databases: List[str] = ["string", "pride", "biogrid"]
) -> dict:
    """Resolve protein identifier across multiple databases"""
    return await _resolve_protein_helper(identifier, target_databases)

@mcp.tool()
async def cross_validate_interactions(
    proteins: List[str],
    databases: List[str] = ["string", "biogrid"],
    confidence_threshold: float = 0.4
) -> dict:
    """Cross-validate protein interactions across databases"""
    return await _cross_validate_interactions_helper(proteins, databases, confidence_threshold)

@mcp.tool()
async def execute_pd_workflow(
    target_proteins: List[str] = ["SNCA", "PARK2", "TH"],
    workflow_type: str = "biomarker_discovery"
) -> dict:
    """Execute complete PD research workflow"""
    
    workflow_results = {
        "workflow_type": workflow_type,
        "target_proteins": target_proteins,
        "steps_completed": [],
        "results": {},
        "recommendations": []
    }
    
    # Step 1: Resolve protein identities using helper
    try:
        resolutions = {}
        for protein in target_proteins:
            resolution = await _resolve_protein_helper(protein)
            resolutions[protein] = resolution
        
        workflow_results["steps_completed"].append("protein_resolution")
        workflow_results["results"]["resolution"] = resolutions
        workflow_results["results"]["resolution_success_rate"] = sum(1 for r in resolutions.values() if r.get("status") == "resolved") / len(resolutions)
    except Exception as e:
        workflow_results["errors"] = [f"Resolution failed: {str(e)}"]
        return workflow_results
    
    # Step 2: Cross-validate interactions using helper
    try:
        validation = await _cross_validate_interactions_helper(target_proteins)
        workflow_results["steps_completed"].append("interaction_validation")
        workflow_results["results"]["validation"] = validation
    except Exception as e:
        workflow_results["errors"] = workflow_results.get("errors", [])
        workflow_results["errors"].append(f"Validation failed: {str(e)}")
    
    # Step 3: Generate recommendations
    successful_resolutions = [p for p, r in workflow_results["results"]["resolution"].items() if r.get("status") == "resolved"]
    convergent_interactions = len(workflow_results["results"]["validation"]["convergent_evidence"])
    
    if len(successful_resolutions) >= 2 and convergent_interactions > 0:
        workflow_results["recommendations"] = [
            f"Strong candidates identified: {successful_resolutions}",
            f"Found {convergent_interactions} interactions with convergent evidence",
            "Proceed with dataset analysis for validation",
            "Consider expanding to related pathway proteins"
        ]
        workflow_results["confidence"] = "high"
    else:
        workflow_results["recommendations"] = [
            "Limited cross-database evidence found",
            "Consider broader protein search",
            "Review individual database results"
        ]
        workflow_results["confidence"] = "moderate"
    
    workflow_results["summary"] = {
        "proteins_resolved": len(successful_resolutions),
        "interactions_validated": len(workflow_results["results"]["validation"]["validated_interactions"]),
        "convergent_evidence": convergent_interactions,
        "overall_confidence": workflow_results["confidence"]
    }
    
    return workflow_results

@mcp.tool()
async def get_biomarker_candidates(
    disease: str = "parkinson",
    confidence_level: str = "high"
) -> dict:
    """Get curated biomarker candidates for specific disease"""
    
    biomarker_data = {
        "parkinson": {
            "high": {
                "proteins": ["SNCA", "PARK2", "TH"],
                "confidence_scores": [0.95, 0.92, 0.88],
                "evidence_types": ["genetic", "proteomic", "functional"]
            },
            "moderate": {
                "proteins": ["LRRK2", "PINK1", "COMT", "UCHL1"],
                "confidence_scores": [0.85, 0.82, 0.78, 0.75],
                "evidence_types": ["genetic", "functional", "expression"]
            }
        }
    }
    
    if disease in biomarker_data and confidence_level in biomarker_data[disease]:
        data = biomarker_data[disease][confidence_level]
        return {
            "disease": disease,
            "confidence_level": confidence_level,
            "candidates": [
                {
                    "protein": protein,
                    "confidence": score,
                    "evidence": evidence
                }
                for protein, score, evidence in zip(data["proteins"], data["confidence_scores"], data["evidence_types"])
            ],
            "total_candidates": len(data["proteins"])
        }
    else:
        return {
            "disease": disease,
            "error": f"No data available for {disease} at {confidence_level} confidence",
            "available": list(biomarker_data.keys())
        }

if __name__ == "__main__":
    # Check if running in Docker (HTTP mode) or locally (stdio mode)  
    if os.getenv("DOCKER_MODE") == "true":
        # Run with HTTP transport for Docker
        mcp.run(transport="http", host="0.0.0.0", port=8000)
    else:
        # Run with stdio transport for local development
        mcp.run()