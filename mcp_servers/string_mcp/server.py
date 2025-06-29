# string_mcp/server.py
from fastmcp import FastMCP
from pydantic import BaseModel
import httpx
import json
import os
from typing import List, Optional, Dict
import asyncio

mcp = FastMCP("STRING Database Server")

# === RESOURCES: Browsable Static Data ===

@mcp.resource("string://species")
async def string_species_resource():
    """Common STRING database species"""
    species_data = {
        "9606": {"name": "Homo sapiens", "common_name": "Human"},
        "10090": {"name": "Mus musculus", "common_name": "Mouse"},
        "10116": {"name": "Rattus norvegicus", "common_name": "Rat"},
        "7227": {"name": "Drosophila melanogaster", "common_name": "Fruit fly"},
        "6239": {"name": "Caenorhabditis elegans", "common_name": "Nematode"},
        "7955": {"name": "Danio rerio", "common_name": "Zebrafish"},
        "3702": {"name": "Arabidopsis thaliana", "common_name": "Thale cress"},
        "559292": {"name": "Saccharomyces cerevisiae", "common_name": "Baker's yeast"}
    }
    
    return json.dumps(species_data, indent=2)

@mcp.resource("string://version")
async def string_version_resource():
    """STRING database version info"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get("https://string-db.org/api/json/version")
            version_data = response.json()
        
        return json.dumps(version_data, indent=2)
    except Exception as e:
        return f"Error fetching version: {str(e)}"

@mcp.resource("string://markers/dopaminergic")
async def dopaminergic_markers_resource():
    """Known dopaminergic neuron markers"""
    markers = {
        "core_markers": {
            "TH": "Tyrosine hydroxylase - rate limiting enzyme",
            "DDC": "DOPA decarboxylase",
            "DAT": "Dopamine transporter",
            "VMAT2": "Vesicular monoamine transporter 2"
        },
        "receptors": {
            "DRD1": "Dopamine receptor D1",
            "DRD2": "Dopamine receptor D2",
            "DRD3": "Dopamine receptor D3",
            "DRD4": "Dopamine receptor D4"
        },
        "pd_associated": {
            "SNCA": "Alpha-synuclein",
            "PARK2": "Parkin",
            "PINK1": "PTEN-induced kinase 1",
            "LRRK2": "Leucine-rich repeat kinase 2"
        },
        "metabolism": {
            "COMT": "Catechol-O-methyltransferase",
            "MAO": "Monoamine oxidase"
        }
    }
    
    return json.dumps(markers, indent=2)

# === TOOLS: Dynamic Operations ===

@mcp.tool()
async def map_proteins(
    proteins: List[str], 
    species: int = 9606
) -> dict:
    """Map protein names to STRING identifiers"""
    await asyncio.sleep(1)  # Rate limiting
    
    url = "https://string-db.org/api/tsv/get_string_ids"
    params = {
        "identifiers": "%0d".join(proteins),  # Use URL-encoded newlines
        "species": species,
        "caller_identity": "mcp_string_server",
        "format": "tsv"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, params=params)  # Use GET instead of POST
        response.raise_for_status()
        
        # Parse TSV response
        lines = response.text.strip().split('\n')
        if len(lines) < 2:
            return {"mapped_proteins": [], "error": "No mapping results"}
            
        headers = lines[0].split('\t')
        results = []
        
        for line in lines[1:]:
            values = line.split('\t')
            if len(values) >= len(headers):
                result = dict(zip(headers, values))
                results.append(result)
        
        return {"mapped_proteins": results}

@mcp.tool()
async def get_network(
    proteins: List[str],
    species: int = 9606,
    confidence: float = 0.4,
    add_white_nodes: int = 10
) -> dict:
    """Retrieve protein-protein interaction network"""
    await asyncio.sleep(1)  # Rate limiting
    
    url = "https://string-db.org/api/tsv/network"
    params = {
        "identifiers": "%0d".join(proteins),  # Use URL-encoded newlines
        "species": species,
        "required_score": int(confidence * 1000),
        "add_white_nodes": add_white_nodes,
        "caller_identity": "mcp_string_server",
        "format": "tsv"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, params=params)  # Use GET instead of POST
        response.raise_for_status()
        
        # Parse TSV response into structured data
        lines = response.text.strip().split('\n')
        if len(lines) < 2:
            return {"network_data": [], "error": "No network data"}
            
        headers = lines[0].split('\t')
        interactions = []
        
        for line in lines[1:]:
            values = line.split('\t')
            if len(values) >= len(headers):
                interaction = dict(zip(headers, values))
                interactions.append(interaction)
        
        return {
            "network_data": interactions,
            "parameters": {
                "proteins": proteins,
                "species": species,
                "confidence": confidence,
                "interaction_count": len(interactions)
            }
        }

@mcp.tool()
async def functional_enrichment(
    proteins: List[str],
    species: int = 9606,
    background: Optional[List[str]] = None
) -> dict:
    """Perform GO/KEGG pathway enrichment analysis"""
    await asyncio.sleep(1)
    
    url = "https://string-db.org/api/tsv/enrichment"
    params = {
        "identifiers": "%0d".join(proteins),  # Use URL-encoded newlines
        "species": species,
        "caller_identity": "mcp_string_server",
        "format": "tsv"
    }
    
    if background:
        params["background_string_identifiers"] = "%0d".join(background)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(url, params=params)  # Use GET instead of POST
        response.raise_for_status()
        
        # Parse enrichment results
        lines = response.text.strip().split('\n')
        if len(lines) < 2:
            return {"enrichment_results": [], "error": "No enrichment data"}
            
        headers = lines[0].split('\t')
        enrichments = []
        
        for line in lines[1:]:
            values = line.split('\t')
            if len(values) >= len(headers):
                enrichment = dict(zip(headers, values))
                enrichments.append(enrichment)
        
        return {"enrichment_results": enrichments}

if __name__ == "__main__":
    if os.getenv("DOCKER_MODE") == "true":
        mcp.run(transport="http", host="0.0.0.0", port=8000)
    else:
        mcp.run()