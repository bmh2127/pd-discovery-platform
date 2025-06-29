# tests/test_cross_database_mcp.py
import pytest
import asyncio
import json

from mcp_servers.cross_database_mcp import mcp as cross_db_mcp
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

# === UNIFIED RESOURCE TESTS ===

@pytest.mark.asyncio
async def test_pd_research_overview():
    """Test comprehensive PD research overview (handles service unavailability)"""
    async with Client(cross_db_mcp) as client:
        overview_resource = await client.read_resource("research://parkinson/overview")
        assert overview_resource is not None
        
        overview_data = extract_resource_content(overview_resource)
        
        # Verify comprehensive structure
        assert "biomarkers" in overview_data
        assert "datasets" in overview_data
        assert "research_workflows" in overview_data
        assert "key_pathways" in overview_data
        assert "database_coverage" in overview_data
        
        # Verify content with fallback support
        assert "SNCA" in overview_data["biomarkers"]["established"]
        assert "LRRK2" in overview_data["biomarkers"]["emerging"]
        
        # Check for datasets (either from live PRIDE service or fallback)
        pride_datasets = overview_data["datasets"]["pride_proteomics"]
        assert isinstance(pride_datasets, list)
        # Should have datasets either from live service or fallback
        if len(pride_datasets) > 0:
            # If we have datasets, they should be valid accession IDs
            assert any(dataset.startswith("PXD") for dataset in pride_datasets)
        
        # Check if service status is reported when services are unavailable
        if "service_status" in overview_data:
            print(f"Service status: {overview_data['service_status']}")
        
        # Verify the note about using tools instead of static resources
        assert "note" in overview_data
        assert "resolve_protein_entity tool" in overview_data["note"]

@pytest.mark.asyncio
async def test_workflow_template():
    """Test workflow template resource"""
    async with Client(cross_db_mcp) as client:
        workflow_resource = await client.read_resource("workflow://pd-biomarker-discovery")
        assert workflow_resource is not None
        
        workflow_data = extract_resource_content(workflow_resource)
        
        # Verify workflow structure
        assert "name" in workflow_data
        assert "steps" in workflow_data
        assert "confidence_thresholds" in workflow_data
        assert "advantages" in workflow_data
        assert len(workflow_data["steps"]) == 5
        assert workflow_data["name"] == "PD Biomarker Discovery Workflow"
        
        # Verify confidence thresholds
        thresholds = workflow_data["confidence_thresholds"]
        assert thresholds["minimum_databases"] == 2
        assert thresholds["minimum_confidence"] == 0.7
        
        # Verify workflow has tool-focused steps
        step_tools = []
        for step in workflow_data["steps"]:
            if "tools" in step:
                step_tools.extend(step["tools"])
        
        # Should have references to our main tools
        assert "resolve_protein_entity" in step_tools
        assert "cross_validate_interactions" in step_tools
        assert "execute_pd_workflow" in step_tools

# === CROSS-DATABASE TOOL TESTS ===

@pytest.mark.asyncio
async def test_resolve_protein_entity():
    """Test cross-database protein resolution (handles service unavailability)"""
    async with Client(cross_db_mcp) as client:
        result = await client.call_tool("resolve_protein_entity", {
            "identifier": "SNCA",
            "target_databases": ["string", "pride"]
        })
        assert result is not None
        result_content = extract_content(result)
        
        # Parse result
        if isinstance(result_content, str):
            result_data = json.loads(result_content)
        else:
            result_data = result_content
            
        assert "query" in result_data
        assert result_data["query"] == "SNCA"
        assert "database_mappings" in result_data
        assert "status" in result_data
        
        # Result can be "resolved" if services are available or "not_found" if they're not
        assert result_data["status"] in ["resolved", "not_found"]
        
        # If resolved, verify structure
        if result_data["status"] == "resolved":
            assert "overall_confidence" in result_data
            assert result_data["overall_confidence"] >= 0
        else:
            # If not resolved, should have suggestion or errors
            assert "suggestion" in result_data or "errors" in result_data

@pytest.mark.asyncio
async def test_cross_validate_interactions():
    """Test cross-database interaction validation (handles service unavailability)"""
    async with Client(cross_db_mcp) as client:
        result = await client.call_tool("cross_validate_interactions", {
            "proteins": ["SNCA", "PARK2"],
            "databases": ["string", "biogrid"],
            "confidence_threshold": 0.4
        })
        assert result is not None
        result_content = extract_content(result)
        
        if isinstance(result_content, str):
            result_data = json.loads(result_content)
        else:
            result_data = result_content
            
        assert "proteins" in result_data
        assert "databases_checked" in result_data
        assert "database_specific" in result_data
        assert "summary" in result_data
        
        # Should always have a summary even if no services are available
        assert "total_interactions_found" in result_data["summary"]
        assert "validation_confidence" in result_data["summary"]

@pytest.mark.asyncio
async def test_get_biomarker_candidates():
    """Test biomarker candidate retrieval"""
    async with Client(cross_db_mcp) as client:
        result = await client.call_tool("get_biomarker_candidates", {
            "disease": "parkinson",
            "confidence_level": "high"
        })
        assert result is not None
        result_content = extract_content(result)
        
        if isinstance(result_content, str):
            result_data = json.loads(result_content)
        else:
            result_data = result_content
            
        assert "disease" in result_data
        assert "candidates" in result_data
        assert result_data["disease"] == "parkinson"
        assert len(result_data["candidates"]) == 3  # SNCA, PARK2, TH
        
        # Check specific candidates
        protein_names = [c["protein"] for c in result_data["candidates"]]
        assert "SNCA" in protein_names
        assert "PARK2" in protein_names
        assert "TH" in protein_names

@pytest.mark.asyncio
async def test_execute_pd_workflow():
    """Test complete PD workflow execution (handles service unavailability)"""
    async with Client(cross_db_mcp) as client:
        result = await client.call_tool("execute_pd_workflow", {
            "target_proteins": ["SNCA", "TH"],
            "workflow_type": "biomarker_discovery"
        })
        assert result is not None
        result_content = extract_content(result)
        
        if isinstance(result_content, str):
            result_data = json.loads(result_content)
        else:
            result_data = result_content
            
        assert "workflow_type" in result_data
        assert "steps_completed" in result_data
        
        # Workflow should complete even if some services are unavailable
        # Check for either successful completion or graceful error handling
        if "summary" in result_data:
            # Successful completion
            assert "overall_confidence" in result_data["summary"]
        elif "errors" in result_data:
            # Graceful error handling
            assert len(result_data["errors"]) > 0
            print(f"Workflow errors (expected if services unavailable): {result_data['errors']}")
        else:
            # Should have either summary or errors
            assert False, "Workflow should have either summary or errors"

# === INTEGRATION TESTS ===

@pytest.mark.asyncio
async def test_complete_research_workflow():
    """Test end-to-end research workflow using resources + tools"""
    async with Client(cross_db_mcp) as client:
        # 1. Browse research overview
        overview = await client.read_resource("research://parkinson/overview")
        overview_data = extract_resource_content(overview)
        target_proteins = overview_data["biomarkers"]["established"][:3]
        
        # 2. Get workflow template
        workflow = await client.read_resource("workflow://pd-biomarker-discovery")
        workflow_data = extract_resource_content(workflow)
        assert len(workflow_data["steps"]) == 5
        
        # 3. Execute workflow with selected proteins
        execution = await client.call_tool("execute_pd_workflow", {
            "target_proteins": target_proteins
        })
        assert execution is not None
        
        # 4. Resolve individual proteins (handle service unavailability)
        resolution_attempts = 0
        successful_resolutions = 0
        
        for protein in target_proteins[:2]:  # Test first 2
            resolution = await client.call_tool("resolve_protein_entity", {
                "identifier": protein
            })
            assert resolution is not None
            resolution_content = extract_content(resolution)
            resolution_data = json.loads(resolution_content) if isinstance(resolution_content, str) else resolution_content
            
            resolution_attempts += 1
            if resolution_data["status"] == "resolved":
                successful_resolutions += 1
                assert "database_mappings" in resolution_data
                assert "overall_confidence" in resolution_data
                print(f"Successfully resolved {protein}")
            else:
                # Should handle gracefully with errors or suggestions
                assert "errors" in resolution_data or "suggestion" in resolution_data
                print(f"Could not resolve {protein} - likely service unavailable")
        
        # Test should pass if we attempted resolutions (regardless of success due to service availability)
        assert resolution_attempts == 2
        print(f"Resolution success rate: {successful_resolutions}/{resolution_attempts}")
        
        # The workflow should complete regardless of individual service availability
        execution_content = extract_content(execution)
        execution_data = json.loads(execution_content) if isinstance(execution_content, str) else execution_content
        assert "workflow_type" in execution_data
        assert "steps_completed" in execution_data

@pytest.mark.asyncio
async def test_systematic_discovery_workflow():
    """Test systematic discovery approach"""
    async with Client(cross_db_mcp) as client:
        # Discovery workflow: Overview → Workflow → Execution → Validation
        
        # Step 1: Research context
        overview = await client.read_resource("research://parkinson/overview")
        overview_data = extract_resource_content(overview)
        
        # Step 2: Select biomarkers for analysis
        established_markers = overview_data["biomarkers"]["established"]
        emerging_markers = overview_data["biomarkers"]["emerging"]
        test_proteins = established_markers[:2] + emerging_markers[:1]
        
        # Step 3: Cross-database validation
        validation = await client.call_tool("cross_validate_interactions", {
            "proteins": test_proteins,
            "databases": ["string", "biogrid"],
            "confidence_threshold": 0.5
        })
        assert validation is not None
        validation_content = extract_content(validation)
        validation_data = json.loads(validation_content) if isinstance(validation_content, str) else validation_content
        
        # Step 4: Individual protein resolution
        resolutions = []
        for protein in test_proteins:
            resolution = await client.call_tool("resolve_protein_entity", {
                "identifier": protein,
                "target_databases": ["string", "pride"]
            })
            resolutions.append(resolution)
        
        assert len(resolutions) == len(test_proteins)
        
        # Step 5: Get biomarker candidates
        candidates = await client.call_tool("get_biomarker_candidates", {
            "disease": "parkinson",
            "confidence_level": "high"
        })
        assert candidates is not None
        
        print("\n=== Systematic Discovery Summary ===")
        print(f"Analyzed proteins: {test_proteins}")
        print(f"Cross-validation completed: {validation is not None}")
        print(f"Individual resolutions: {len(resolutions)}")
        print(f"Biomarker candidates retrieved: {candidates is not None}")

@pytest.mark.asyncio
async def test_protein_not_found_handling():
    """Test handling of proteins not found in live databases"""
    async with Client(cross_db_mcp) as client:
        # Test with non-existent protein
        result = await client.call_tool("resolve_protein_entity", {
            "identifier": "NONEXISTENT_PROTEIN_12345"
        })
        assert result is not None
        result_content = extract_content(result)
        result_data = json.loads(result_content) if isinstance(result_content, str) else result_content
        
        # Should handle non-existent proteins gracefully
        assert result_data["status"] == "not_found"
        assert "suggestion" in result_data or "errors" in result_data
        
        # Should provide helpful guidance
        if "suggestion" in result_data:
            assert "available" in result_data["suggestion"] or "correct" in result_data["suggestion"]

@pytest.mark.asyncio
async def test_resource_data_consistency():
    """Test consistency between resources and tools"""
    async with Client(cross_db_mcp) as client:
        # Get proteins from overview
        overview = await client.read_resource("research://parkinson/overview")
        overview_data = extract_resource_content(overview)
        established_proteins = overview_data["biomarkers"]["established"]
        
        # Test that these proteins can be resolved using the tool (no static resource anymore)
        for protein in established_proteins[:3]:  # Test first 3
            resolution = await client.call_tool("resolve_protein_entity", {
                "identifier": protein
            })
            result_content = extract_content(resolution)
            result_data = json.loads(result_content) if isinstance(result_content, str) else result_content
            
            # Should be able to resolve established biomarkers (or handle gracefully if services unavailable)
            assert result_data["status"] in ["resolved", "not_found"], f"Unexpected status for biomarker {protein}"
            
            # If resolved, should have proper structure
            if result_data["status"] == "resolved":
                assert "database_mappings" in result_data
                assert "overall_confidence" in result_data
                print(f"Successfully resolved {protein} with confidence {result_data.get('overall_confidence', 'N/A')}")
            else:
                # If not resolved due to service unavailability, should have errors or suggestions
                has_error_info = "errors" in result_data or "suggestion" in result_data
                assert has_error_info, f"Should have error info when protein {protein} cannot be resolved"
                print(f"Could not resolve {protein} - likely due to service unavailability")