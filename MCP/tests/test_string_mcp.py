# tests/test_string_mcp.py
import pytest
import asyncio

from MCP.string_mcp import mcp as string_mcp
from fastmcp import Client

@pytest.mark.asyncio
async def test_map_proteins():
    async with Client(string_mcp) as client:
        # Test the map_proteins tool
        result = await client.call_tool("map_proteins", {
            "proteins": ["SNCA", "PARK2", "TH"],
            "species": 9606
        })
        assert result is not None
        # The result should contain mapped protein data
        result_str = str(result)
        assert "mapped_proteins" in result_str

@pytest.mark.asyncio 
async def test_get_network():
    async with Client(string_mcp) as client:
        # Test the get_network tool
        result = await client.call_tool("get_network", {
            "proteins": ["SNCA", "PARK2"],
            "species": 9606
        })
        assert result is not None
        # The result should contain network data
        result_str = str(result)
        assert "network_data" in result_str

@pytest.mark.asyncio
async def test_dopaminergic_enrichment():
    async with Client(string_mcp) as client:
        # First get dopaminergic markers
        markers_result = await client.call_tool("get_dopaminergic_markers", {})
        assert markers_result is not None
        
        # Then test functional enrichment (this would normally use the markers)
        # For testing purposes, we'll use a simple protein list
        enrichment_result = await client.call_tool("functional_enrichment", {
            "proteins": ["TH", "SNCA", "PARK2"],
            "species": 9606
        })
        assert enrichment_result is not None
        result_str = str(enrichment_result)
        assert "enrichment_results" in result_str

@pytest.mark.asyncio
async def test_get_dopaminergic_markers():
    async with Client(string_mcp) as client:
        # Test getting dopaminergic markers
        result = await client.call_tool("get_dopaminergic_markers", {})
        assert result is not None
        # Should contain known markers like TH, SNCA, etc.
        result_str = str(result)
        assert "TH" in result_str or "dopaminergic_markers" in result_str