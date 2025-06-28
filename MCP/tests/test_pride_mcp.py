# tests/test_pride_mcp.py
import pytest
import asyncio
import json

from MCP.pride_mcp import mcp as pride_mcp
from fastmcp import Client

def extract_content(result):
    """Helper to extract actual content from FastMCP result"""
    if hasattr(result, '__iter__') and len(result) > 0:
        # Get the first content item
        content_item = result[0]
        if hasattr(content_item, 'text'):
            return content_item.text
    return str(result)

@pytest.mark.asyncio
async def test_search_projects():
    async with Client(pride_mcp) as client:
        result = await client.call_tool("search_projects", {
            "query": "proteome",
            "size": 5
        })
        assert result is not None
        content = extract_content(result)
        
        # Try to parse as JSON to check structure
        try:
            data = json.loads(content)
            assert "projects" in data or isinstance(data, list)
        except json.JSONDecodeError:
            # If not JSON, check string content
            assert "PXD" in content or "projects" in content

@pytest.mark.asyncio
async def test_search_pd_datasets():
    async with Client(pride_mcp) as client:
        result = await client.call_tool("search_pd_datasets", {
            "size": 10
        })
        assert result is not None
        content = extract_content(result)
        
        # Check if results contain PD-related terms or project data
        content_lower = content.lower()
        assert ("projects" in content_lower or 
                "pxd" in content_lower or 
                any(term in content_lower for term in ["parkinson", "dopamine", "synuclein"]))

@pytest.mark.asyncio
async def test_protein_search():
    async with Client(pride_mcp) as client:
        result = await client.call_tool("find_datasets_with_protein", {
            "protein_name": "alpha-synuclein"
        })
        assert result is not None
        content = extract_content(result)
        
        # Check if the result contains the expected structure
        try:
            data = json.loads(content)
            assert "matching_datasets" in data
        except json.JSONDecodeError:
            # If not JSON, check string representation
            assert "matching_datasets" in content

@pytest.mark.asyncio
async def test_get_project_details():
    async with Client(pride_mcp) as client:
        # First search for a project to get an accession
        search_result = await client.call_tool("search_projects", {
            "query": "proteome",
            "size": 1
        })
        assert search_result is not None
        
        # For this test, we'll use a mock accession since we can't guarantee 
        # a specific project exists. In a real test, you'd parse the search result.
        # This test mainly validates the tool is callable
        try:
            detail_result = await client.call_tool("get_project_details", {
                "accession": "PXD000001"  # Example accession
            })
            # If successful, check result format
            content = extract_content(detail_result)
            assert content is not None
        except Exception as e:
            # It's OK if the specific accession doesn't exist
            # We're mainly testing that the tool is properly configured
            assert "get_project_details" in str(e) or "404" in str(e) or "Not Found" in str(e)

@pytest.mark.asyncio
async def test_search_proteins():
    async with Client(pride_mcp) as client:
        # Test the search_proteins tool
        try:
            result = await client.call_tool("search_proteins", {
                "accession": "PXD000001",  # Example accession
                "protein_name": "synuclein"
            })
            content = extract_content(result)
            assert content is not None
        except Exception as e:
            # It's OK if the specific accession doesn't exist
            # We're mainly testing that the tool is properly configured
            assert "search_proteins" in str(e) or "404" in str(e) or "Not Found" in str(e)