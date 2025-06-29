# biogrid-mcp/server.py
import os
from fastmcp import FastMCP
import httpx
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP("BioGRID Database Server")

BIOGRID_API_KEY = os.getenv("BIOGRID_API_KEY") 

@mcp.tool()
async def search_interactions(
    gene_names: List[str],
    organism: str = "9606",  # Human
    interaction_type: str = "physical"
) -> dict:
    """Search for protein interactions in BioGRID"""
    
    if not BIOGRID_API_KEY:
        return {"error": "BioGRID API key required"}
    
    url = "https://webservice.thebiogrid.org/interactions/"
    params = {
        "accesskey": BIOGRID_API_KEY,
        "format": "json",
        "geneList": "|".join(gene_names),
        "organism": organism,
        "searchNames": "true",
        "includeInteractors": "true"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()

@mcp.tool()
async def get_organisms() -> dict:
    """Get list of supported organisms"""
    
    if not BIOGRID_API_KEY:
        return {"error": "BioGRID API key required"}
    
    url = "https://webservice.thebiogrid.org/organisms/"
    params = {
        "accesskey": BIOGRID_API_KEY,
        "format": "json"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()

if __name__ == "__main__":
    # Check if running in Docker (HTTP mode) or locally (stdio mode)
    if os.getenv("DOCKER_MODE") == "true":
        # Run with HTTP transport for Docker
        mcp.run(transport="http", host="0.0.0.0", port=8000)
    else:
        # Run with stdio transport for local development
        mcp.run()