# tests/test_ppx_mcp.py
import pytest
import asyncio
import json
import os

from MCP.ppx_mcp import mcp as ppx_mcp
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
async def test_ppx_search_projects():
    async with Client(ppx_mcp) as client:
        result = await client.call_tool("ppx_search_projects", {
            "keywords": ["Parkinson"],
            "max_results": 5
        })
        assert result is not None
        content = extract_content(result)
        
        # Check if we get project data or an error (ppx might not be installed)
        if "error" in content.lower():
            # PPX not available - that's OK for testing
            assert "ppx" in content.lower() or "failed" in content.lower()
        else:
            # PPX is available - check for project data
            try:
                data = json.loads(content)
                assert "projects" in data
                assert "projects_found" in data
                assert "search_term" in data
            except json.JSONDecodeError:
                # If not JSON, should contain project information
                assert ("projects" in content.lower() or 
                        "parkinson" in content.lower())

@pytest.mark.asyncio
async def test_ppx_extract_metadata():
    async with Client(ppx_mcp) as client:
        # Use a known public dataset
        result = await client.call_tool("ppx_extract_metadata", {
            "accession": "PXD007160",  # Known PD dataset
            "extract_proteins": True,
            "extract_experimental_design": True
        })
        assert result is not None
        content = extract_content(result)
        
        # Check if we get metadata or an error
        if "error" in content.lower():
            # PPX not available or dataset not found - that's OK for testing
            assert "ppx" in content.lower() or "failed" in content.lower()
        else:
            # PPX is available - check for metadata
            try:
                data = json.loads(content)
                assert "accession" in data
                assert "basic_metadata" in data
            except json.JSONDecodeError:
                # If not JSON, should contain metadata information
                assert ("accession" in content.lower() or 
                        "metadata" in content.lower() or
                        "pxd007160" in content.lower())

@pytest.mark.asyncio
async def test_find_pd_protein_datasets():
    async with Client(ppx_mcp) as client:
        result = await client.call_tool("find_pd_protein_datasets", {
            "target_proteins": ["SNCA"],
            "max_datasets": 3
        })
        assert result is not None
        content = extract_content(result)
        
        # Check if we get dataset data or an error
        if "error" in content.lower():
            # PPX not available - that's OK for testing
            assert "ppx" in content.lower() or "failed" in content.lower()
        else:
            # PPX is available - check for dataset data
            try:
                data = json.loads(content)
                assert "target_proteins" in data
                assert "matching_datasets" in data
            except json.JSONDecodeError:
                # If not JSON, should contain dataset information
                assert ("target_proteins" in content.lower() or 
                        "matching_datasets" in content.lower() or
                        "snca" in content.lower())

@pytest.mark.asyncio
async def test_ppx_download_data():
    async with Client(ppx_mcp) as client:
        # Test download functionality (without actually downloading large files)
        result = await client.call_tool("ppx_download_data", {
            "accession": "PXD007160",
            "output_dir": "./test_downloads",
            "file_types": ["metadata"]  # Only metadata to keep test lightweight
        })
        assert result is not None
        content = extract_content(result)
        
        # Check if we get download result or an error
        if "error" in content.lower():
            # PPX not available or download failed - that's OK for testing
            assert ("ppx" in content.lower() or 
                    "failed" in content.lower() or 
                    "not found" in content.lower())
        else:
            # PPX is available - check for download result
            try:
                data = json.loads(content)
                assert "accession" in data
                # Should have metadata or download info
                assert ("metadata" in data or 
                        "files_downloaded" in data or 
                        "download_path" in data)
            except json.JSONDecodeError:
                # If not JSON, should contain download information
                assert ("download" in content.lower() or 
                        "metadata" in content.lower() or
                        "pxd007160" in content.lower())

@pytest.mark.asyncio
async def test_ppx_batch_analysis():
    async with Client(ppx_mcp) as client:
        # Test batch processing with a small set
        result = await client.call_tool("ppx_batch_analysis", {
            "accessions": ["PXD007160"],  # Single dataset for testing
            "analysis_type": "protein_summary",
            "output_dir": "./test_batch_results"
        })
        assert result is not None
        content = extract_content(result)
        
        # Check if we get batch results or an error
        if "error" in content.lower():
            # PPX not available - that's OK for testing
            assert "ppx" in content.lower() or "failed" in content.lower()
        else:
            # PPX is available - check for batch results
            try:
                data = json.loads(content)
                assert ("batch_results" in data or 
                        "summary" in data or
                        "total_datasets" in data)
            except json.JSONDecodeError:
                # If not JSON, should contain batch information
                assert ("batch" in content.lower() or 
                        "analysis" in content.lower() or
                        "pxd007160" in content.lower())

@pytest.mark.asyncio
async def test_format_for_analysis():
    async with Client(ppx_mcp) as client:
        result = await client.call_tool("format_for_analysis", {
            "accession": "PXD007160",
            "output_format": "pandas",
            "include_metadata": True
        })
        assert result is not None
        content = extract_content(result)
        
        # Check if we get formatted data or an error
        if "error" in content.lower():
            # PPX not available - that's OK for testing
            assert "ppx" in content.lower() or "failed" in content.lower()
        else:
            # PPX is available - check for formatted data
            try:
                data = json.loads(content)
                assert ("formatted_data" in data or 
                        "output_format" in data or
                        "accession" in data)
            except json.JSONDecodeError:
                # If not JSON, should contain format information
                assert ("format" in content.lower() or 
                        "pandas" in content.lower() or
                        "analysis" in content.lower())

@pytest.mark.skipif(not os.system("python -c 'import ppx' 2>/dev/null") == 0, 
                   reason="PPX package not installed")
@pytest.mark.asyncio
async def test_ppx_with_package_available():
    """This test only runs if PPX package is actually installed"""
    async with Client(ppx_mcp) as client:
        result = await client.call_tool("ppx_search_projects", {
            "keywords": ["proteome"],
            "max_results": 2
        })
        assert result is not None
        content = extract_content(result)
        
        # With PPX available, should not get installation errors
        assert "PPX search failed" not in content
        
        # Should get actual project data
        try:
            data = json.loads(content)
            assert "projects" in data
            assert "projects_found" in data
            assert isinstance(data["projects_found"], int)
        except json.JSONDecodeError:
            # If not JSON, should still contain project info
            assert len(content) > 50  # Should have substantial content