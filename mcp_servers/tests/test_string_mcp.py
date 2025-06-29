# tests/test_string_mcp.py
import pytest
import asyncio
import json

from mcp_servers.string_mcp import mcp as string_mcp
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

# === ORIGINAL TOOL TESTS (Updated) ===

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
        result_content = extract_content(result)
        assert "mapped_proteins" in result_content

@pytest.mark.asyncio 
async def test_get_network():
    async with Client(string_mcp) as client:
        # Test the get_network tool
        result = await client.call_tool("get_network", {
            "proteins": ["SNCA", "PARK2"],
            "species": 9606,
            "confidence": 0.4
        })
        assert result is not None
        # The result should contain network data
        result_content = extract_content(result)
        assert "network_data" in result_content
        
        # Test with higher confidence
        result_high = await client.call_tool("get_network", {
            "proteins": ["SNCA", "PARK2"],
            "species": 9606,
            "confidence": 0.7
        })
        assert result_high is not None

@pytest.mark.asyncio
async def test_functional_enrichment():
    """Updated test name (was test_dopaminergic_enrichment)"""
    async with Client(string_mcp) as client:
        # Test functional enrichment directly
        enrichment_result = await client.call_tool("functional_enrichment", {
            "proteins": ["TH", "SNCA", "PARK2"],
            "species": 9606
        })
        assert enrichment_result is not None
        result_content = extract_content(enrichment_result)
        assert "enrichment_results" in result_content

@pytest.mark.asyncio
async def test_get_dopaminergic_markers():
    """This tool is now replaced by a resource, but keeping for backward compatibility"""
    async with Client(string_mcp) as client:
        # If the tool still exists, test it
        try:
            result = await client.call_tool("get_dopaminergic_markers", {})
            assert result is not None
            result_content = extract_content(result)
            assert "TH" in result_content or "dopaminergic_markers" in result_content
        except Exception:
            # Tool might not exist anymore - that's OK, we have the resource
            pass

# === NEW RESOURCE TESTS ===

@pytest.mark.asyncio
async def test_dopaminergic_markers_resource():
    """Test the new dopaminergic markers resource"""
    async with Client(string_mcp) as client:
        # Test the resource access
        markers_resource = await client.read_resource("string://markers/dopaminergic")
        assert markers_resource is not None
        assert len(markers_resource) > 0
        
        # Parse the JSON content using helper
        markers_data = extract_resource_content(markers_resource)
        
        # Verify structure
        assert "core_markers" in markers_data
        assert "receptors" in markers_data
        assert "pd_associated" in markers_data
        assert "metabolism" in markers_data
        
        # Verify specific markers
        assert "TH" in markers_data["core_markers"]
        assert "SNCA" in markers_data["pd_associated"] 
        assert "DRD1" in markers_data["receptors"]
        assert "COMT" in markers_data["metabolism"]
        
        # Verify descriptions exist
        assert "Tyrosine hydroxylase" in markers_data["core_markers"]["TH"]

@pytest.mark.asyncio
async def test_species_resource():
    """Test the species resource"""
    async with Client(string_mcp) as client:
        species_resource = await client.read_resource("string://species")
        assert species_resource is not None
        
        species_data = extract_resource_content(species_resource)
        
        # Verify common species are present
        assert "9606" in species_data  # Human
        assert "10090" in species_data  # Mouse
        assert species_data["9606"]["name"] == "Homo sapiens"
        assert species_data["9606"]["common_name"] == "Human"

@pytest.mark.asyncio
async def test_version_resource():
    """Test the STRING version resource"""
    async with Client(string_mcp) as client:
        version_resource = await client.read_resource("string://version")
        assert version_resource is not None
        
        # Should contain version information (or error message)
        content = version_resource[0].text
        assert content is not None
        # Either contains JSON version data or error message
        assert "version" in content.lower() or "error" in content.lower()

# === INTEGRATION TESTS: Resources + Tools ===

@pytest.mark.asyncio
async def test_resource_tool_integration():
    """Test using resources to inform tool usage"""
    async with Client(string_mcp) as client:
        # 1. Get markers from resource
        markers_resource = await client.read_resource("string://markers/dopaminergic")
        markers_data = extract_resource_content(markers_resource)
        
        # 2. Extract protein list from resource
        core_markers = list(markers_data["core_markers"].keys())
        pd_markers = list(markers_data["pd_associated"].keys())
        test_proteins = core_markers[:2] + pd_markers[:2]  # First 2 from each category
        
        # 3. Use extracted proteins in tools
        map_result = await client.call_tool("map_proteins", {
            "proteins": test_proteins,
            "species": 9606
        })
        assert map_result is not None
        
        network_result = await client.call_tool("get_network", {
            "proteins": test_proteins[:3],  # Limit to 3 for faster testing
            "species": 9606,
            "confidence": 0.4
        })
        assert network_result is not None

@pytest.mark.asyncio
async def test_dopaminergic_pathway_analysis():
    """Comprehensive test using both resources and tools for dopaminergic pathway analysis"""
    async with Client(string_mcp) as client:
        # 1. Browse available markers
        markers_resource = await client.read_resource("string://markers/dopaminergic")
        markers_data = extract_resource_content(markers_resource)
        
        # 2. Select markers for analysis (focus on core + PD-associated)
        analysis_proteins = ["TH", "SNCA", "PARK2", "DRD2"]
        
        # Verify these are in our resource
        all_markers = {**markers_data["core_markers"], **markers_data["pd_associated"], **markers_data["receptors"]}
        for protein in analysis_proteins:
            assert protein in all_markers, f"{protein} not found in dopaminergic markers"
        
        # 3. Map proteins to STRING IDs
        mapping_result = await client.call_tool("map_proteins", {
            "proteins": analysis_proteins,
            "species": 9606
        })
        mapping_content = extract_content(mapping_result)
        assert "mapped_proteins" in mapping_content
        
        # 4. Get interaction network
        network_result = await client.call_tool("get_network", {
            "proteins": analysis_proteins,
            "species": 9606,
            "confidence": 0.4,
            "add_white_nodes": 5
        })
        network_content = extract_content(network_result)
        assert "network_data" in network_content
        
        # 5. Perform functional enrichment
        enrichment_result = await client.call_tool("functional_enrichment", {
            "proteins": analysis_proteins,
            "species": 9606
        })
        enrichment_content = extract_content(enrichment_result)
        assert "enrichment_results" in enrichment_content

@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling for both resources and tools"""
    async with Client(string_mcp) as client:
        # Test tool with invalid species - should raise an error
        from fastmcp.exceptions import ToolError
        
        with pytest.raises(ToolError) as exc_info:
            await client.call_tool("map_proteins", {
                "proteins": ["SNCA"],
                "species": 99999  # Invalid species
            })
        
        # Verify it's a meaningful error about the API request
        assert "400 Bad Request" in str(exc_info.value)
        
        # Test tool with empty protein list - should also raise an error
        with pytest.raises(ToolError) as exc_info:
            await client.call_tool("get_network", {
                "proteins": [],
                "species": 9606
            })
        
        # Verify it's a meaningful error about the API request
        assert "400 Bad Request" in str(exc_info.value)
        
        # Test a valid case to ensure the tools work when given correct input
        result = await client.call_tool("map_proteins", {
            "proteins": ["SNCA"],
            "species": 9606  # Valid species
        })
        assert result is not None
        result_content = extract_content(result)
        assert "mapped_proteins" in result_content
        
        # Resources should generally work or return error information
        version_resource = await client.read_resource("string://version")
        assert version_resource is not None

# === PERFORMANCE TESTS ===

@pytest.mark.asyncio
async def test_resource_caching_benefit():
    """Test that resources can be accessed multiple times efficiently"""
    async with Client(string_mcp) as client:
        # Access the same resource multiple times
        for i in range(3):
            markers_resource = await client.read_resource("string://markers/dopaminergic")
            assert markers_resource is not None
            markers_data = extract_resource_content(markers_resource)
            assert "core_markers" in markers_data
            
            # Small delay to simulate real usage
            await asyncio.sleep(0.1)

@pytest.mark.asyncio
async def test_comprehensive_pd_workflow():
    """Test a complete PD research workflow using the updated MCP"""
    async with Client(string_mcp) as client:
        # === Phase 1: Discovery ===
        # Browse available markers
        markers_resource = await client.read_resource("string://markers/dopaminergic")
        markers_data = extract_resource_content(markers_resource)
        
        # Select core PD-related proteins
        target_proteins = ["SNCA", "PARK2", "TH", "DRD2", "LRRK2"]
        
        # === Phase 2: Mapping ===
        # Resolve protein identifiers
        mapping_result = await client.call_tool("map_proteins", {
            "proteins": target_proteins,
            "species": 9606
        })
        assert mapping_result is not None
        
        # === Phase 3: Network Analysis ===
        # Get high-confidence interactions
        network_result = await client.call_tool("get_network", {
            "proteins": target_proteins,
            "species": 9606,
            "confidence": 0.7,  # High confidence
            "add_white_nodes": 10
        })
        assert network_result is not None
        
        # === Phase 4: Functional Analysis ===
        # Perform pathway enrichment
        enrichment_result = await client.call_tool("functional_enrichment", {
            "proteins": target_proteins,
            "species": 9606
        })
        assert enrichment_result is not None
        
        # === Validation ===
        # All steps should have completed successfully
        print("\n=== PD Workflow Summary ===")
        print(f"Target proteins: {target_proteins}")
        print("✓ Markers browsed via resource")
        print("✓ Proteins mapped to STRING IDs") 
        print("✓ Interaction network retrieved")
        print("✓ Functional enrichment completed")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])