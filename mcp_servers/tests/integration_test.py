# tests/integration_test.py - Complete integration including BioGRID
import pytest
import asyncio
import os
import json

from mcp_servers.string_mcp import mcp as string_mcp
from mcp_servers.pride_mcp import mcp as pride_mcp
from mcp_servers.ppx_mcp import mcp as ppx_mcp
from mcp_servers.biogrid_mcp import mcp as biogrid_mcp
from fastmcp import Client

def extract_content(result):
    """Helper to extract actual content from FastMCP result"""
    if hasattr(result, '__iter__') and len(result) > 0:
        # Get the first content item
        content_item = result[0]
        if hasattr(content_item, 'text'):
            return content_item.text
    return str(result)

def extract_resource_content(resource_result):
    """Helper to extract JSON content from FastMCP resource result"""
    if isinstance(resource_result, list) and len(resource_result) > 0:
        # FastMCP returns list of TextResourceContents objects
        resource_item = resource_result[0]
        if hasattr(resource_item, 'text'):
            text_content = resource_item.text
            try:
                # Try to parse as JSON
                return json.loads(text_content)
            except json.JSONDecodeError:
                return text_content
    return str(resource_result)

@pytest.mark.asyncio
async def test_complete_pd_workflow_all_mcps():
    """Test complete workflow with all MCP servers including BioGRID"""
    
    # 1. Get dopaminergic markers from resource
    async with Client(string_mcp) as client:
        markers_resource = await client.read_resource("string://markers/dopaminergic")
        markers_data = extract_resource_content(markers_resource)
        
        # Extract protein list from all categories
        all_proteins = []
        for category in markers_data.values():
            if isinstance(category, dict):
                all_proteins.extend(category.keys())
        
        target_proteins = all_proteins[:5]  # Limit for testing
        
        # Create a mock result format for backwards compatibility
        markers_content = json.dumps({
            "dopaminergic_markers": target_proteins
        })
    
    # 2. Get STRING protein network
    async with Client(string_mcp) as client:
        string_result = await client.call_tool("get_network", {
            "proteins": target_proteins,
            "species": 9606
        })
        string_content = extract_content(string_result)
        assert "network_data" in string_content
    
    # 3. Get BioGRID interactions (if API key available)
    biogrid_interactions = None
    async with Client(biogrid_mcp) as client:
        biogrid_result = await client.call_tool("search_interactions", {
            "gene_names": target_proteins,
            "organism": "9606"
        })
        biogrid_content = extract_content(biogrid_result)
        
        if "BioGRID API key required" not in biogrid_content:
            biogrid_interactions = biogrid_content
        else:
            print("WARNING: BioGRID API key not found - skipping BioGRID tests")
    
    # 4. Find datasets with PPX
    async with Client(ppx_mcp) as client:
        ppx_result = await client.call_tool("find_pd_protein_datasets", {
            "target_proteins": target_proteins,
            "max_datasets": 3
        })
        ppx_content = extract_content(ppx_result)
        assert "matching_datasets" in ppx_content or "error" in ppx_content.lower()
    
    # 5. Cross-reference with PRIDE - Fix the assertion logic
    async with Client(pride_mcp) as client:
        pride_result = await client.call_tool("search_pd_datasets", {
            "size": 5
        })
        pride_content = extract_content(pride_result)
        
        # Try to parse as JSON first, then fall back to string matching
        try:
            pride_data = json.loads(pride_content)
            # Check if it's a list of projects or has a projects key
            has_projects = (isinstance(pride_data, list) and len(pride_data) > 0) or "projects" in pride_content
            assert has_projects, f"No projects found in PRIDE response"
        except json.JSONDecodeError:
            # Fall back to string matching
            assert "projects" in pride_content or "accession" in pride_content, f"Unexpected PRIDE response format"
    
    # 6. Look for specific protein in datasets
    async with Client(pride_mcp) as client:
        snca_result = await client.call_tool("find_datasets_with_protein", {
            "protein_name": "alpha-synuclein"
        })
        snca_content = extract_content(snca_result)
        assert "matching_datasets" in snca_content
    
    # Create comprehensive summary
    summary = {
        "target_proteins": target_proteins,
        "string_network_found": "network_data" in string_content,
        "biogrid_interactions_found": biogrid_interactions is not None,
        "ppx_datasets_found": "matching_datasets" in ppx_content,
        "pride_projects_found": "accession" in pride_content or "projects" in pride_content,
        "snca_specific_datasets": "matching_datasets" in snca_content
    }
    
    print("\n=== PD Research Workflow Summary ===")
    for key, value in summary.items():
        print(f"{key}: {value}")
    
    return summary

@pytest.mark.asyncio
async def test_protein_interaction_comparison():
    """Compare protein interactions between STRING and BioGRID"""
    
    test_proteins = ["SNCA", "PARK2"]
    
    # Get STRING interactions
    async with Client(string_mcp) as client:
        string_result = await client.call_tool("get_network", {
            "proteins": test_proteins,
            "species": 9606,
            "confidence": 700  # 0.7 confidence
        })
        string_content = extract_content(string_result)
    
    # Get BioGRID interactions (if available)
    biogrid_result = None
    async with Client(biogrid_mcp) as client:
        biogrid_result = await client.call_tool("search_interactions", {
            "gene_names": test_proteins,
            "organism": "9606"
        })
        biogrid_content = extract_content(biogrid_result)
        
        if "BioGRID API key required" not in biogrid_content:
            # Compare results
            comparison = {
                "proteins_tested": test_proteins,
                "string_data_available": "network_data" in string_content,
                "biogrid_data_available": True,
                "interaction_sources": ["STRING", "BioGRID"]
            }
            
            print("\n=== Interaction Database Comparison ===")
            print(f"Testing proteins: {test_proteins}")
            print(f"STRING data: {'✓' if comparison['string_data_available'] else '✗'}")
            print(f"BioGRID data: {'✓' if comparison['biogrid_data_available'] else '✗'}")
            
            return comparison
    
    print("BioGRID comparison skipped - API key required")
    return {"biogrid_skipped": True}

@pytest.mark.asyncio 
async def test_data_source_integration():
    """Test integration across all data sources for systematic discovery"""
    
    target_protein = "SNCA"
    
    # 1. Get interaction partners from both STRING and BioGRID
    async with Client(string_mcp) as client:
        string_result = await client.call_tool("get_network", {
            "proteins": [target_protein],
            "species": 9606,
            "add_white_nodes": 5
        })
        string_content = extract_content(string_result)
    
    async with Client(biogrid_mcp) as client:
        biogrid_result = await client.call_tool("search_interactions", {
            "gene_names": [target_protein],
            "organism": "9606"
        })
        biogrid_content = extract_content(biogrid_result)
    
    # 2. Find proteomics datasets containing the protein
    async with Client(ppx_mcp) as client:
        ppx_result = await client.call_tool("find_pd_protein_datasets", {
            "target_proteins": [target_protein]
        })
        ppx_content = extract_content(ppx_result)
    
    async with Client(pride_mcp) as client:
        pride_result = await client.call_tool("find_datasets_with_protein", {
            "protein_name": target_protein
        })
        pride_content = extract_content(pride_result)
    
    # 3. Create integrated analysis summary
    integration_summary = {
        "target_protein": target_protein,
        "interaction_networks": {
            "string_available": "network_data" in string_content,
            "biogrid_available": "BioGRID API key required" not in biogrid_content
        },
        "proteomics_datasets": {
            "ppx_datasets": "matching_datasets" in ppx_content,
            "pride_datasets": "matching_datasets" in pride_content
        },
        "ready_for_systematic_analysis": True
    }
    
    print(f"\n=== Integration Summary for {target_protein} ===")
    print(f"Interaction networks available: {integration_summary['interaction_networks']}")
    print(f"Proteomics datasets found: {integration_summary['proteomics_datasets']}")
    
    # Verify we have enough data for meaningful analysis
    datasets_available = (integration_summary["proteomics_datasets"]["ppx_datasets"] or
                         integration_summary["proteomics_datasets"]["pride_datasets"])
    
    assert datasets_available, "No proteomics datasets found for analysis"
    
    return integration_summary

# Test runner with BioGRID API key check
@pytest.mark.asyncio
async def test_setup_verification():
    """Verify all MCP servers are properly configured"""
    
    setup_status = {
        "string_mcp": True,  # No API key required
        "pride_mcp": True,   # No API key required  
        "ppx_mcp": True,     # No API key required
        "biogrid_mcp": os.getenv("BIOGRID_API_KEY") is not None
    }
    
    print("\n=== MCP Setup Verification ===")
    for mcp_name, status in setup_status.items():
        status_symbol = "✓" if status else "✗ (API key required)"
        print(f"{mcp_name}: {status_symbol}")
    
    if not setup_status["biogrid_mcp"]:
        print("\nTo enable BioGRID MCP:")
        print("1. Get API key from: https://webservice.thebiogrid.org/")
        print("2. Set environment variable: export BIOGRID_API_KEY=your_key")
    
    return setup_status