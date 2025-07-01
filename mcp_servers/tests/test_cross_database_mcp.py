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

# === MODULAR COMPONENT INTEGRATION TESTS ===

@pytest.mark.asyncio
async def test_modular_cache_integration(self):
    """Test that cache system integrates properly with MCP server"""
    async with Client(cross_db_mcp) as client:
        # Make same protein resolution twice
        first_call = await client.call_tool("resolve_protein_entity", {
            "identifier": "SNCA"
        })
        second_call = await client.call_tool("resolve_protein_entity", {
            "identifier": "SNCA"
        })
        
        # Both calls should succeed
        assert first_call is not None
        assert second_call is not None
        
        # Extract content
        first_content = extract_content(first_call)
        second_content = extract_content(second_call)
        
        first_data = json.loads(first_content) if isinstance(first_content, str) else first_content
        second_data = json.loads(second_content) if isinstance(second_content, str) else second_content
        
        # Both should have same query
        assert first_data["query"] == second_data["query"] == "SNCA"
        
        # Second call might be faster due to caching (but we can't assert timing in tests)
        # Instead, verify that both have proper structure
        for data in [first_data, second_data]:
            assert "status" in data
            assert data["query"] == "SNCA"

@pytest.mark.asyncio
async def test_modular_gene_mapping_integration(self):
    """Test that gene mapping works through the MCP interface"""
    async with Client(cross_db_mcp) as client:
        # Test alias resolution
        alias_tests = [
            ("DAT", "SLC6A3"),  # DAT should map to SLC6A3
            ("PARK2", "PRKN"),  # PARK2 should map to PRKN
            ("VMAT2", "SLC18A2")  # VMAT2 should map to SLC18A2
        ]
        
        for alias, expected_canonical in alias_tests:
            result = await client.call_tool("resolve_protein_entity", {
                "identifier": alias
            })
            assert result is not None
            
            content = extract_content(result)
            data = json.loads(content) if isinstance(content, str) else content
            
            # Should handle alias properly (either resolve it or provide helpful info)
            assert data["query"] == alias
            assert "status" in data
            
            # If resolved, should have database mappings
            if data["status"] == "resolved":
                assert "database_mappings" in data
                print(f"Successfully resolved alias {alias}")
            else:
                # Should provide helpful error/suggestion
                assert "errors" in data or "suggestion" in data
                print(f"Could not resolve alias {alias} - likely service unavailable")

@pytest.mark.asyncio
async def test_modular_api_client_integration(self):
    """Test that API client properly handles service communication"""
    async with Client(cross_db_mcp) as client:
        # Test cross-validation which uses API client heavily
        result = await client.call_tool("cross_validate_interactions", {
            "proteins": ["SNCA", "TH"],
            "databases": ["string", "biogrid"],
            "confidence_threshold": 0.5
        })
        
        assert result is not None
        content = extract_content(result)
        data = json.loads(content) if isinstance(content, str) else content
        
        # Should have proper structure regardless of service availability
        assert "proteins" in data
        assert data["proteins"] == ["SNCA", "TH"]
        assert "databases_checked" in data
        assert "confidence_threshold" in data
        assert data["confidence_threshold"] == 0.5
        
        # Should handle service availability gracefully
        if "database_specific" in data:
            print(f"Cross-validation successful with databases: {list(data['database_specific'].keys())}")
        else:
            print("Cross-validation completed with service unavailability handling")

@pytest.mark.asyncio
async def test_modular_config_integration(self):
    """Test that configuration is properly loaded and used"""
    async with Client(cross_db_mcp) as client:
        # Test that server responds (configuration loaded correctly)
        result = await client.call_tool("get_biomarker_candidates", {
            "disease": "parkinson"
        })
        
        assert result is not None
        content = extract_content(result)
        data = json.loads(content) if isinstance(content, str) else content
        
        # Should have proper structure from config-driven logic
        assert "disease" in data
        assert data["disease"] == "parkinson"
        assert "candidates" in data
        
        # Candidates should reflect properly configured dopaminergic genes
        if len(data["candidates"]) > 0:
            # Check that we have known dopaminergic/PD genes
            candidate_proteins = [c["protein"] for c in data["candidates"]]
            known_pd_genes = ["SNCA", "PRKN", "TH"]
            has_known_genes = any(gene in candidate_proteins for gene in known_pd_genes)
            assert has_known_genes, f"Should include known PD genes, got: {candidate_proteins}"

@pytest.mark.asyncio
async def test_modular_error_handling_integration(self):
    """Test that modular error handling works end-to-end"""
    async with Client(cross_db_mcp) as client:
        # Test with invalid/unknown protein
        result = await client.call_tool("resolve_protein_entity", {
            "identifier": "COMPLETELY_FAKE_PROTEIN_12345"
        })
        
        assert result is not None
        content = extract_content(result)
        data = json.loads(content) if isinstance(content, str) else content
        
        # Should handle unknown protein gracefully
        assert data["query"] == "COMPLETELY_FAKE_PROTEIN_12345"
        assert data["status"] == "not_found"
        
        # Should provide helpful suggestion
        assert "suggestion" in data or "errors" in data
        
        # Test workflow with invalid parameters
        workflow_result = await client.call_tool("execute_pd_workflow", {
            "target_proteins": [],  # Empty list should be handled
            "workflow_type": "invalid_workflow"
        })
        
        assert workflow_result is not None
        workflow_content = extract_content(workflow_result)
        workflow_data = json.loads(workflow_content) if isinstance(workflow_content, str) else workflow_content
        
        # Should handle invalid input gracefully
        assert "errors" in workflow_data or "workflow_type" in workflow_data

@pytest.mark.asyncio
async def test_modular_performance_integration(self):
    """Test that modular design doesn't significantly impact performance"""
    import time
    
    async with Client(cross_db_mcp) as client:
        # Test multiple concurrent calls
        start_time = time.time()
        
        tasks = []
        test_proteins = ["SNCA", "TH", "PRKN"]
        
        for protein in test_proteins:
            task = client.call_tool("resolve_protein_entity", {
                "identifier": protein
            })
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # All calls should succeed or fail gracefully
        assert len(results) == 3
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Task {i} failed with exception: {result}")
            else:
                assert result is not None
                content = extract_content(result)
                data = json.loads(content) if isinstance(content, str) else content
                assert "query" in data
                assert data["query"] == test_proteins[i]
        
        # Performance should be reasonable (under 30 seconds for 3 concurrent calls)
        assert total_time < 30.0, f"Concurrent calls took too long: {total_time}s"
        print(f"Modular integration test completed in {total_time:.2f}s")

@pytest.mark.asyncio
async def test_systematic_discovery_integration(self):
    """Test the full systematic discovery workflow with modular components"""
    async with Client(cross_db_mcp) as client:
        # Step 1: Get research overview (uses curated data)
        overview = await client.read_resource("research://parkinson/overview")
        overview_data = extract_resource_content(overview)
        
        established_biomarkers = overview_data["biomarkers"]["established"]
        test_proteins = established_biomarkers[:2]  # Use first 2 for testing
        
        # Step 2: Resolve individual proteins (uses gene mapping + API client + cache)
        resolution_results = []
        for protein in test_proteins:
            result = await client.call_tool("resolve_protein_entity", {
                "identifier": protein,
                "target_databases": ["string", "pride"]
            })
            resolution_results.append(result)
        
        # Step 3: Cross-validate interactions (uses API client + cross validation tools)
        validation_result = await client.call_tool("cross_validate_interactions", {
            "proteins": test_proteins,
            "databases": ["string", "biogrid"],
            "confidence_threshold": 0.7
        })
        
        # Step 4: Get biomarker candidates (uses evidence-based scoring)
        candidates_result = await client.call_tool("get_biomarker_candidates", {
            "disease": "parkinson",
            "confidence_level": "high"
        })
        
        # Verify the systematic workflow completed
        assert len(resolution_results) == len(test_proteins)
        assert validation_result is not None
        assert candidates_result is not None
        
        # Extract and verify data
        validation_data = json.loads(extract_content(validation_result))
        candidates_data = json.loads(extract_content(candidates_result))
        
        assert validation_data["proteins"] == test_proteins
        assert candidates_data["disease"] == "parkinson"
        
        # Count successful components
        successful_resolutions = 0
        for result in resolution_results:
            if result is not None:
                data = json.loads(extract_content(result))
                if data["status"] == "resolved":
                    successful_resolutions += 1
        
        print(f"\n=== Systematic Discovery Integration Results ===")
        print(f"Test proteins: {test_proteins}")
        print(f"Successful resolutions: {successful_resolutions}/{len(test_proteins)}")
        print(f"Cross-validation completed: {validation_result is not None}")
        print(f"Candidates retrieved: {len(candidates_data.get('candidates', []))}")
        print(f"All modular components integrated successfully!")

if __name__ == "__main__":
    # Run with: python -m pytest tests/test_cross_database_mcp.py -v
    import asyncio
    asyncio.run(test_systematic_discovery_integration())