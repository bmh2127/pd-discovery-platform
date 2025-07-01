# cross_database_mcp/server.py - CLEAN main server file
from fastmcp import FastMCP
import os
import json
import asyncio
from datetime import datetime
from typing import List

# Import utilities
from .utils.cache_manager import protein_cache
from .utils.gene_mappings import gene_mapper
from .data.evidence_data import get_evidence_based_pd_relevance, get_dopaminergic_classification
from .tools.cross_validation_tools import _resolve_protein_helper, _cross_validate_interactions_helper
from .tools.dopaminergic_network_tools import build_dopaminergic_reference_network

mcp = FastMCP("Cross-Database Integration Server")

# === RESOURCES ===

@mcp.resource("protein://resolved/{identifier}")
async def protein_resolved_resource(identifier: str):
    """Cached protein entity with cross-database resolution"""
    
    # Check cache first
    cached_data = protein_cache.get(identifier)
    if cached_data:
        return json.dumps(cached_data, indent=2)
    
    try:
        resolution_data = await asyncio.wait_for(
            _resolve_protein_helper(identifier), 
            timeout=30.0
        )
    except asyncio.TimeoutError:
        return json.dumps({
            "query": identifier,
            "status": "timeout",
            "error": "Resolution timed out after 30 seconds"
        }, indent=2)
    
    # Build enhanced data
    enhanced_data = {
        **resolution_data,
        "systematic_discovery": {
            "aliases": gene_mapper.get_aliases(identifier),
            "disease_relevance": get_evidence_based_pd_relevance(identifier),
            "dopaminergic_classification": get_dopaminergic_classification(identifier)
        },
        "research_context": {
            "systematic_discovery_ready": resolution_data.get("status") == "resolved",
            "cross_database_confidence": resolution_data.get("overall_confidence", 0.0),
            "research_priority": _determine_research_priority(identifier)
        },
        "cross_references": {
            "sub_resources": [
                f"protein://resolved/{identifier}/interactions",
                f"protein://resolved/{identifier}/datasets"
            ]
        },
        "cache_metadata": {
            "resolved_at": datetime.now().isoformat(),
            "valid_for": "24h",
            "confidence_level": resolution_data.get("overall_confidence", 0.0)
        }
    }
    
    # Cache and return
    protein_cache.set(identifier, enhanced_data)
    return json.dumps(enhanced_data, indent=2)

@mcp.resource("research://parkinson/overview")
async def pd_research_overview_resource():
    """Comprehensive Parkinson's disease research overview"""
    
    overview = {
        "biomarkers": {
            "established": ["SNCA", "PRKN", "TH", "DRD2"],  # Fixed PARK2 -> PRKN
            "emerging": ["LRRK2", "PINK1", "COMT", "UCHL1"],
            "total_count": 8
        },
        "datasets": {
            "pride_proteomics": ["PXD015293", "PXD037684", "PXD047134", "PXD030142", "PXD020722"],
            "total_datasets": 5
        },
        "research_workflows": [
            "workflow://pd-biomarker-discovery",
            "workflow://cross-database-validation"
        ],
        "key_pathways": [
            "Dopamine synthesis", "Mitochondrial function", 
            "Protein aggregation", "Neuroinflammation", "Autophagy/mitophagy"
        ],
        "database_coverage": {
            "STRING": "protein interactions",
            "PRIDE": "proteomics datasets", 
            "BioGRID": "validated interactions"
        }
    }
    
    return json.dumps(overview, indent=2)

@mcp.resource("workflow://pd-biomarker-discovery")
async def pd_biomarker_workflow_resource():
    """PD biomarker discovery workflow template"""
    
    workflow = {
        "name": "PD Biomarker Discovery Workflow",
        "description": "Systematic cross-database biomarker identification",
        "steps": [
            {"step": 1, "name": "Browse research overview", "resources": ["research://parkinson/overview"]},
            {"step": 2, "name": "Resolve target proteins", "tools": ["resolve_protein_entity"]},
            {"step": 3, "name": "Cross-validate interactions", "tools": ["cross_validate_interactions"]},
            {"step": 4, "name": "Batch process proteins", "tools": ["batch_resolve_proteins"]},
            {"step": 5, "name": "Execute workflow", "tools": ["execute_pd_workflow"]}
        ],
        "confidence_thresholds": {"minimum_databases": 2, "minimum_confidence": 0.7}
    }
    
    return json.dumps(workflow, indent=2)

# === TOOLS ===

@mcp.tool()
async def build_dopaminergic_reference_network_tool(
    discovery_mode: str = "comprehensive",
    confidence_threshold: float = 0.7,
    include_indirect: bool = True,
    max_white_nodes: int = 20
) -> dict:
    """
    Build comprehensive dopaminergic reference network for systematic discovery
    
    This tool enables paradigm-challenging research by systematically mapping
    the complete dopaminergic interaction network and identifying unexpected
    connections that may reveal early disruption patterns.
    
    Discovery modes:
    - "minimal": Core synthesis and transport proteins
    - "standard": Complete dopaminergic pathway  
    - "comprehensive": Full pathway + PD-associated proteins
    - "hypothesis_free": Start minimal and discover connections
    """
    return await build_dopaminergic_reference_network(
        discovery_mode, confidence_threshold, include_indirect, max_white_nodes
    )

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
async def batch_resolve_proteins(
    identifiers: List[str],
    target_databases: List[str] = ["string", "pride", "biogrid"]
) -> dict:
    """Batch resolve multiple proteins efficiently"""
    
    results = {
        "identifiers": identifiers,
        "total_count": len(identifiers),
        "resolutions": {},
        "summary": {}
    }
    
    # Process proteins concurrently with limited concurrency
    semaphore = asyncio.Semaphore(5)  # Max 5 concurrent resolutions
    
    async def resolve_single(identifier: str):
        async with semaphore:
            return identifier, await _resolve_protein_helper(identifier, target_databases)
    
    # Execute batch resolution
    tasks = [resolve_single(identifier) for identifier in identifiers]
    resolved_results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    successful_resolutions = 0
    for result in resolved_results:
        if isinstance(result, Exception):
            continue
        identifier, resolution_data = result
        results["resolutions"][identifier] = resolution_data
        if resolution_data.get("status") == "resolved":
            successful_resolutions += 1
    
    # Generate summary
    results["summary"] = {
        "successful_resolutions": successful_resolutions,
        "success_rate": successful_resolutions / len(identifiers) if identifiers else 0,
        "failed_resolutions": len(identifiers) - successful_resolutions,
        "databases_used": target_databases
    }
    
    return results

@mcp.tool()
async def execute_pd_workflow(
    target_proteins: List[str] = ["SNCA", "PRKN", "TH"],  # Fixed PARK2 -> PRKN
    workflow_type: str = "biomarker_discovery"
) -> dict:
    """Execute complete PD research workflow"""
    
    workflow_results = {
        "workflow_type": workflow_type,
        "target_proteins": target_proteins,
        "steps_completed": [],
        "results": {}
    }
    
    # Step 1: Batch resolve proteins
    try:
        batch_resolution = await batch_resolve_proteins(target_proteins)
        workflow_results["steps_completed"].append("batch_protein_resolution")
        workflow_results["results"]["resolution"] = batch_resolution
    except Exception as e:
        workflow_results["errors"] = [f"Batch resolution failed: {str(e)}"]
        return workflow_results
    
    # Step 2: Cross-validate interactions
    try:
        validation = await _cross_validate_interactions_helper(target_proteins)
        workflow_results["steps_completed"].append("interaction_validation")
        workflow_results["results"]["validation"] = validation
    except Exception as e:
        workflow_results["errors"] = workflow_results.get("errors", [])
        workflow_results["errors"].append(f"Validation failed: {str(e)}")
    
    # Step 3: Generate summary
    success_rate = workflow_results["results"]["resolution"]["summary"]["success_rate"]
    total_interactions = workflow_results["results"]["validation"]["summary"]["total_interactions_found"]
    
    workflow_results["summary"] = {
        "protein_resolution_rate": success_rate,
        "total_interactions_found": total_interactions,
        "workflow_confidence": "high" if success_rate > 0.8 and total_interactions > 5 else "moderate"
    }
    
    return workflow_results

@mcp.tool()
async def get_biomarker_candidates(
    disease: str = "parkinson",
    confidence_level: str = "high"
) -> dict:
    """Get curated biomarker candidates"""
    
    biomarker_data = {
        "parkinson": {
            "high": {
                "proteins": ["SNCA", "PRKN", "TH"],  # Fixed PARK2 -> PRKN
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
                {"protein": protein, "confidence": score, "evidence": evidence}
                for protein, score, evidence in zip(
                    data["proteins"], data["confidence_scores"], data["evidence_types"]
                )
            ],
            "total_candidates": len(data["proteins"])
        }
    else:
        return {
            "disease": disease,
            "error": f"No data available for {disease} at {confidence_level} confidence"
        }

# === HELPER FUNCTIONS ===

def _determine_research_priority(identifier: str) -> str:
    """Determine research priority based on systematic discovery criteria"""
    dopaminergic_data = get_dopaminergic_classification(identifier)
    
    if dopaminergic_data.get("is_dopaminergic") and dopaminergic_data.get("relevance", 0) > 0.8:
        return "high_priority_established"
    elif dopaminergic_data.get("indirect_dopaminergic_effect"):
        return "high_priority_pathology"
    elif dopaminergic_data.get("relevance", 0) > 0.7:
        return "moderate_priority"
    else:
        return "discovery_candidate"

if __name__ == "__main__":
    if os.getenv("DOCKER_MODE") == "true":
        mcp.run(transport="http", host="0.0.0.0", port=8000)
    else:
        mcp.run()