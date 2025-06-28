# string-mcp/server.py
from fastmcp import FastMCP
from pydantic import BaseModel
import httpx
import json
from typing import List, Optional
import asyncio

class StringProtein(BaseModel):
    string_id: str
    name: str
    description: Optional[str]
    
class InteractionNetwork(BaseModel):
    proteins: List[StringProtein]
    interactions: List[dict]
    confidence_scores: List[float]

mcp = FastMCP("STRING Database Server")

@mcp.tool()
async def map_proteins(
    proteins: List[str], 
    species: int = 9606,  # Human
    format: str = "tsv"
) -> dict:
    """Map protein names to STRING identifiers"""
    await asyncio.sleep(1)  # Rate limiting
    
    url = "https://string-db.org/api/tsv/get_string_ids"
    params = {
        "identifiers": "\r".join(proteins),
        "species": species,
        "format": format
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=params)
        response.raise_for_status()
        return {"mapped_proteins": response.text}

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
        "identifiers": "\r".join(proteins),
        "species": species,
        "required_score": int(confidence * 1000),
        "add_white_nodes": add_white_nodes
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=params)
        response.raise_for_status()
        return {"network_data": response.text}

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
        "identifiers": "\r".join(proteins),
        "species": species,
        "caller_identity": "pd_research_project"
    }
    
    if background:
        params["background_string_identifiers"] = "\r".join(background)
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=params)
        response.raise_for_status()
        return {"enrichment_results": response.text}

@mcp.tool()
async def get_dopaminergic_markers() -> dict:
    """Get known dopaminergic neuron marker proteins"""
    dopamine_markers = [
        "TH",      # Tyrosine hydroxylase
        "DDC",     # DOPA decarboxylase  
        "DAT",     # Dopamine transporter
        "DRD1",    # Dopamine receptor D1
        "DRD2",    # Dopamine receptor D2
        "VMAT2",   # Vesicular monoamine transporter 2
        "COMT",    # Catechol-O-methyltransferase
        "MAO",     # Monoamine oxidase
        "SNCA",    # Alpha-synuclein
        "PARK2",   # Parkin
        "PINK1",   # PINK1
        "LRRK2"    # LRRK2
    ]
    return {"dopaminergic_markers": dopamine_markers}

if __name__ == "__main__":
    mcp.run()