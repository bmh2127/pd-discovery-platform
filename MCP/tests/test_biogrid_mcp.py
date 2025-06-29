# tests/test_biogrid_mcp.py
import pytest
import asyncio
import json
import os

from MCP.biogrid_mcp import mcp as biogrid_mcp
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
async def test_search_interactions():
    async with Client(biogrid_mcp) as client:
        # Test with common Parkinson's disease genes
        result = await client.call_tool("search_interactions", {
            "gene_names": ["SNCA", "PARK2"],
            "organism": "9606",  # Human
            "interaction_type": "physical"
        })
        assert result is not None
        content = extract_content(result)
        
        # Check if we get interaction data or an API key error
        if "error" in content.lower() and "api key" in content.lower():
            # API key not configured - that's OK for testing
            assert "BioGRID API key required" in content
        else:
            # API key is configured - check for interaction data
            try:
                data = json.loads(content)
                # BioGRID returns interaction data as a dictionary
                assert isinstance(data, dict)
            except json.JSONDecodeError:
                # If not JSON, should contain interaction information
                assert ("interaction" in content.lower() or 
                        "snca" in content.lower() or 
                        "park2" in content.lower())

@pytest.mark.asyncio
async def test_search_interactions_single_gene():
    async with Client(biogrid_mcp) as client:
        # Test with a single well-known gene
        result = await client.call_tool("search_interactions", {
            "gene_names": ["TP53"],
            "organism": "9606"
        })
        assert result is not None
        content = extract_content(result)
        
        # Check response format
        if "error" in content.lower() and "api key" in content.lower():
            assert "BioGRID API key required" in content
        else:
            # Should contain interaction data for TP53
            assert "tp53" in content.lower() or "interaction" in content.lower()

@pytest.mark.asyncio  
async def test_get_organisms():
    async with Client(biogrid_mcp) as client:
        result = await client.call_tool("get_organisms", {})
        assert result is not None
        content = extract_content(result)
        
        # Check if we get organism data or an API key error
        if "error" in content.lower() and "api key" in content.lower():
            # API key not configured - that's OK for testing
            assert "BioGRID API key required" in content
        else:
            # API key is configured - check for organism data
            try:
                data = json.loads(content)
                assert isinstance(data, dict)
                # Should contain organism information
            except json.JSONDecodeError:
                # If not JSON, should contain organism information
                assert ("organism" in content.lower() or 
                        "species" in content.lower() or
                        "9606" in content)  # Human organism ID

@pytest.mark.asyncio
async def test_search_interactions_multiple_genes():
    async with Client(biogrid_mcp) as client:
        # Test with multiple Parkinson's disease-related genes
        result = await client.call_tool("search_interactions", {
            "gene_names": ["SNCA", "PARK2", "PINK1", "LRRK2"],
            "organism": "9606",
            "interaction_type": "physical"
        })
        assert result is not None
        content = extract_content(result)
        
        if "error" in content.lower() and "api key" in content.lower():
            assert "BioGRID API key required" in content
        else:
            # Should handle multiple genes
            gene_names = ["snca", "park2", "pink1", "lrrk2"]
            found_genes = any(gene in content.lower() for gene in gene_names)
            assert found_genes or "interaction" in content.lower()

@pytest.mark.asyncio
async def test_search_interactions_different_organism():
    async with Client(biogrid_mcp) as client:
        # Test with a different model organism (mouse)
        result = await client.call_tool("search_interactions", {
            "gene_names": ["Snca"],  # Mouse gene naming
            "organism": "10090",  # Mouse
            "interaction_type": "physical"  
        })
        assert result is not None
        content = extract_content(result)
        
        if "error" in content.lower() and "api key" in content.lower():
            assert "BioGRID API key required" in content
        else:
            # Should contain interaction data for mouse
            assert "snca" in content.lower() or "interaction" in content.lower()

@pytest.mark.skipif(not os.getenv("BIOGRID_API_KEY"), reason="BioGRID API key not configured")
@pytest.mark.asyncio
async def test_api_key_configured():
    """This test only runs if BioGRID API key is actually configured"""
    async with Client(biogrid_mcp) as client:
        result = await client.call_tool("get_organisms", {})
        assert result is not None
        content = extract_content(result)
        
        # With API key, should not get error
        assert "BioGRID API key required" not in content
        
        # Should get actual organism data
        try:
            data = json.loads(content)
            assert isinstance(data, dict)
            assert len(data) > 0  # Should have organism data
        except json.JSONDecodeError:
            # If not JSON, should still contain organism info
            assert len(content) > 50  # Should have substantial content 