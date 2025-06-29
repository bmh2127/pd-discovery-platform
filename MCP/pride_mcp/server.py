# pride-mcp/server.py
from fastmcp import FastMCP
from pydantic import BaseModel
import httpx
import os
from typing import List, Optional
import asyncio

class PrideProject(BaseModel):
    accession: str
    title: str
    description: str
    species: List[str]
    instruments: List[str]
    publication_date: str

mcp = FastMCP("PRIDE Database Server")

# Helper functions (not decorated - can be called internally)
async def _search_projects_helper(
    query: str = "",
    species: str = "Homo sapiens",
    disease: str = "",
    page: int = 0,
    size: int = 20
) -> dict:
    """Internal helper for searching PRIDE projects"""
    
    url = "https://www.ebi.ac.uk/pride/ws/archive/v2/projects"
    params = {
        "show": size,
        "page": page,
        "sortDirection": "DESC",
        "sortConditions": "submission_date"
    }
    
    if query:
        params["keyword"] = query
    if species:
        params["species"] = species
    if disease:
        params["keyword"] = f"{query} {disease}".strip()
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()

async def _search_proteins_helper(
    accession: str,
    protein_name: str = "",
    page: int = 0,
    size: int = 100
) -> dict:
    """Internal helper for searching proteins in a project"""
    
    url = f"https://www.ebi.ac.uk/pride/ws/archive/v2/projects/{accession}/proteins"
    params = {
        "show": size,
        "page": page
    }
    
    if protein_name:
        params["keyword"] = protein_name
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()

# MCP Tools (decorated functions)
@mcp.tool()
async def search_projects(
    query: str = "",
    species: str = "Homo sapiens",
    disease: str = "",
    page: int = 0,
    size: int = 20
) -> dict:
    """Search PRIDE projects with filters"""
    return await _search_projects_helper(query, species, disease, page, size)

@mcp.tool()
async def search_pd_datasets(
    keywords: List[str] = ["Parkinson", "dopamine", "alpha-synuclein"],
    species: str = "Homo sapiens",
    page: int = 0,
    size: int = 50
) -> dict:
    """Find Parkinson's disease specific datasets"""
    
    search_terms = " OR ".join(keywords)
    return await _search_projects_helper(
        query=search_terms,
        species=species,
        page=page,
        size=size
    )

@mcp.tool()
async def get_project_details(accession: str) -> dict:
    """Get detailed information about a specific project"""
    
    url = f"https://www.ebi.ac.uk/pride/ws/archive/v2/projects/{accession}"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()

@mcp.tool()
async def get_project_files(accession: str) -> dict:
    """Get file listing for a project"""
    
    url = f"https://www.ebi.ac.uk/pride/ws/archive/v2/projects/{accession}/files"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()

@mcp.tool()
async def search_proteins(
    accession: str,
    protein_name: str = "",
    page: int = 0,
    size: int = 100
) -> dict:
    """Search for proteins within a specific project"""
    return await _search_proteins_helper(accession, protein_name, page, size)

@mcp.tool()
async def find_datasets_with_protein(
    protein_name: str,
    disease_context: str = "Parkinson"
) -> dict:
    """Find datasets containing specific proteins in disease context"""
    
    # Use helper function instead of calling decorated function
    projects = await _search_projects_helper(
        query=f"{disease_context} OR {protein_name}",
        page=0,
        size=10
    )
    
    results = []
    if "projects" in projects:
        for project in projects["projects"][:10]:  # Limit to first 10 for testing
            accession = project["accession"]
            try:
                proteins = await _search_proteins_helper(accession, protein_name)
                if proteins.get("proteins") and len(proteins["proteins"]) > 0:
                    results.append({
                        "project": project,
                        "protein_matches": proteins["proteins"]
                    })
            except:
                continue  # Skip projects with errors
    
    return {"matching_datasets": results}

if __name__ == "__main__":
    # Check if running in Docker (HTTP mode) or locally (stdio mode)
    if os.getenv("DOCKER_MODE") == "true":
        # Run with HTTP transport for Docker
        mcp.run(transport="http", host="0.0.0.0", port=8000)
    else:
        # Run with stdio transport for local development
        mcp.run()
    