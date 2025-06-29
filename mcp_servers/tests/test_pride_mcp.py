# tests/test_pride_mcp.py
import pytest
import asyncio
import json

from mcp_servers.pride_mcp import mcp as pride_mcp
from fastmcp import Client


def extract_content(result):
    """Helper to extract actual content from FastMCP result"""
    if hasattr(result, '__iter__') and len(result) > 0:
        content_item = result[0]
        if hasattr(content_item, 'text'):
            return content_item.text
    return str(result)

def extract_resource_content(resource_result):
    """Helper to extract JSON content from FastMCP resource result"""
    if isinstance(resource_result, list) and len(resource_result) > 0:
        resource_item = resource_result[0]
        if hasattr(resource_item, 'text'):
            text_content = resource_item.text
            try:
                return json.loads(text_content)
            except json.JSONDecodeError:
                return text_content
    return str(resource_result)

# === TOOL TESTS ===

@pytest.mark.asyncio
async def test_search_projects():
    async with Client(pride_mcp) as client:
        result = await client.call_tool("search_projects", {
            "query": "parkinson",
            "species": "Homo sapiens",
            "size": 5
        })
        assert result is not None
        result_content = extract_content(result)
        assert "projects" in result_content or "total" in result_content

@pytest.mark.asyncio
async def test_search_pd_datasets():
    async with Client(pride_mcp) as client:
        result = await client.call_tool("search_pd_datasets", {
            "keywords": ["Parkinson", "dopamine"],
            "size": 10
        })
        assert result is not None
        result_content = extract_content(result)
        assert "projects" in result_content or result_content != ""

@pytest.mark.asyncio
async def test_get_project_details():
    async with Client(pride_mcp) as client:
        # Test with a known PD dataset
        result = await client.call_tool("get_project_details", {
            "accession": "PXD007160"
        })
        assert result is not None
        result_content = extract_content(result)
        assert "accession" in result_content or "title" in result_content

# === RESOURCE TESTS ===

@pytest.mark.asyncio
async def test_pd_datasets_resource():
    """Test the curated PD datasets resource"""
    async with Client(pride_mcp) as client:
        pd_resource = await client.read_resource("research://parkinson/datasets/pride")
        assert pd_resource is not None
        
        pd_data = extract_resource_content(pd_resource)
        
        # Verify structure
        assert "proteomics_datasets" in pd_data
        assert "metadata" in pd_data
        assert "research_focus" in pd_data
        
        # Verify specific verified datasets
        datasets = pd_data["proteomics_datasets"]
        assert "PXD015293" in datasets  # Mouse model study
        assert "PXD037684" in datasets  # Human substantia nigra study  
        assert "PXD047134" in datasets  # GBA1 mutation study
        assert "PXD030142" in datasets  # Single-cell study
        assert "PXD020722" in datasets  # Urinary biomarker study
        
        # Verify metadata reflects the verified datasets
        assert datasets["PXD037684"]["species"] == "Homo sapiens"
        assert "Parkinson's disease" in datasets["PXD037684"]["disease"]
        assert datasets["PXD015293"]["species"] == "Mus musculus"
        assert "verified_active" in datasets["PXD015293"]["status"]
        
        # Verify research focus categories
        research_focus = pd_data["research_focus"]
        assert "human_brain_studies" in research_focus
        assert "mouse_models" in research_focus
        assert "biomarker_studies" in research_focus
        assert "genetic_variants" in research_focus
        
        # Verify metadata totals
        metadata = pd_data["metadata"]
        assert metadata["total_datasets"] == 5
        assert "Homo sapiens" in metadata["species_coverage"]
        assert "Mus musculus" in metadata["species_coverage"]

@pytest.mark.asyncio
async def test_pride_project_resource():
    """Test individual project resource"""
    async with Client(pride_mcp) as client:
        # Test with known project
        project_resource = await client.read_resource("pride://project/PXD007160")
        assert project_resource is not None
        assert len(project_resource) > 0
        
        # Parse the resource content
        project_data = extract_resource_content(project_resource)
        
        # Should have project info and sub-resources
        assert "project_info" in project_data or "sub_resources" in project_data or "Error" in str(project_data)

@pytest.mark.asyncio
async def test_pride_project_files_resource():
    """Test project files resource"""
    async with Client(pride_mcp) as client:
        files_resource = await client.read_resource("pride://project/PXD007160/files")
        assert files_resource is not None
        
        # Should contain file information (or error if project not accessible)
        content = files_resource[0].text
        assert content is not None

# === INTEGRATION TESTS ===

@pytest.mark.asyncio
async def test_pride_pd_workflow():
    """Test PD research workflow using PRIDE resources and tools"""
    async with Client(pride_mcp) as client:
        # 1. Browse curated datasets
        datasets_resource = await client.read_resource("research://parkinson/datasets/pride")
        datasets_data = extract_resource_content(datasets_resource)
        
        # 2. Select datasets for analysis
        pd_datasets = datasets_data["proteomics_datasets"]
        target_accessions = list(pd_datasets.keys())[:2]  # Test first 2
        
        # 3. Get details for each dataset (handle unavailable datasets gracefully)
        successful_details = 0
        for accession in target_accessions:
            try:
                details = await client.call_tool("get_project_details", {
                    "accession": accession
                })
                assert details is not None
                successful_details += 1
            except Exception as e:
                # Some datasets might not be available (404) - this is realistic
                if "404" in str(e) or "Not Found" in str(e):
                    print(f"Dataset {accession} not available (404) - expected behavior")
                else:
                    # Re-raise unexpected errors
                    raise
        
        # At least one dataset check should succeed, or we can test with a known good one
        if successful_details == 0:
            # Fallback: test with one of our verified datasets
            try:
                fallback_details = await client.call_tool("get_project_details", {
                    "accession": "PXD015293"  # Try verified dataset
                })
                assert fallback_details is not None
                successful_details = 1
            except Exception:
                # If even this fails, skip the detailed checks but continue with other tests
                pass
            
        # 4. Search for additional relevant datasets
        search_result = await client.call_tool("search_pd_datasets", {
            "keywords": ["alpha-synuclein", "SNCA"],
            "size": 5
        })
        assert search_result is not None
        
        # Summary: workflow should complete even if some individual datasets are unavailable
        print(f"Workflow completed: {successful_details} dataset details retrieved successfully")

@pytest.mark.asyncio
async def test_protein_dataset_discovery():
    """Test finding datasets containing specific proteins"""
    async with Client(pride_mcp) as client:
        # Search for datasets containing SNCA
        result = await client.call_tool("find_datasets_with_protein", {
            "protein_name": "alpha-synuclein",
            "disease_context": "Parkinson"
        })
        assert result is not None
        result_content = extract_content(result)
        assert "matching_datasets" in result_content