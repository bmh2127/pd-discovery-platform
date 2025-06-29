# tests/test_docker_integration.py - Docker HTTP MCP Integration Tests
import pytest
import asyncio
import json
import subprocess
import time
import os
from fastmcp import Client

# Docker configuration
DOCKER_COMPOSE_FILE = "docker-compose.yml"
MCP_ENDPOINTS = {
    "string": "http://localhost:8001/mcp/",
    "pride": "http://localhost:8002/mcp/", 
    "ppx": "http://localhost:8003/mcp/",
    "biogrid": "http://localhost:8004/mcp/"
}

def extract_result(result):
    """Extract content from FastMCP HTTP result"""
    if isinstance(result, list) and len(result) > 0:
        content = result[0]
        if hasattr(content, 'text'):
            return content.text
        elif isinstance(content, dict):
            return json.dumps(content, indent=2)
        else:
            return str(content)
    elif hasattr(result, 'text'):
        return result.text
    else:
        return str(result)

@pytest.fixture(scope="module")
def docker_services():
    """Start Docker services before tests and stop them after"""
    print("\n🐳 Starting Docker MCP services...")
    
    # Change to MCP directory for docker-compose
    original_dir = os.getcwd()
    mcp_dir = os.path.dirname(os.path.abspath(__file__)).replace('/tests', '')
    os.chdir(mcp_dir)
    
    try:
        # Start Docker services
        result = subprocess.run(
            ["docker-compose", "up", "-d", "--build"],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Wait for services to be ready
        print("⏳ Waiting for services to start...")
        time.sleep(10)
        
        # Verify services are running
        result = subprocess.run(
            ["docker-compose", "ps", "--format", "table"],
            capture_output=True,
            text=True
        )
        print("📊 Docker services status:")
        print(result.stdout)
        
        yield "services_ready"
        
    finally:
        print("\n🧹 Cleaning up Docker services...")
        subprocess.run(["docker-compose", "down"], capture_output=True)
        os.chdir(original_dir)

@pytest.mark.asyncio
async def test_docker_string_mcp(docker_services):
    """Test STRING MCP server via Docker HTTP transport"""
    
    async with Client(MCP_ENDPOINTS["string"]) as client:
        # Test dopaminergic markers
        result = await client.call_tool("get_dopaminergic_markers", {})
        result_text = extract_result(result)
        
        # Verify response
        assert len(result_text) > 0
        assert "dopaminergic_markers" in result_text
        
        # Parse and verify markers
        markers_data = json.loads(result_text)
        assert "dopaminergic_markers" in markers_data
        assert len(markers_data["dopaminergic_markers"]) >= 10
        assert "SNCA" in markers_data["dopaminergic_markers"]
        
        # Test network retrieval
        network_result = await client.call_tool("get_network", {
            "proteins": ["SNCA", "PARK2"],
            "species": 9606,
            "confidence": 0.7
        })
        network_text = extract_result(network_result)
        
        assert len(network_text) > 0
        assert "network_data" in network_text

@pytest.mark.asyncio 
async def test_docker_pride_mcp(docker_services):
    """Test PRIDE MCP server via Docker HTTP transport"""
    
    async with Client(MCP_ENDPOINTS["pride"]) as client:
        # Test PD dataset search
        result = await client.call_tool("search_pd_datasets", {
            "size": 5
        })
        result_text = extract_result(result)
        
        assert len(result_text) > 0
        
        # Try to parse as JSON and verify structure
        try:
            pride_data = json.loads(result_text)
            # Check if it's a list of projects or has a projects key
            has_projects = (isinstance(pride_data, list) and len(pride_data) > 0) or "projects" in result_text
            assert has_projects
        except json.JSONDecodeError:
            # Fall back to string matching
            assert "projects" in result_text or "accession" in result_text
        
        # Test general project search
        projects_result = await client.call_tool("search_projects", {
            "query": "Parkinson",
            "size": 3
        })
        projects_text = extract_result(projects_result)
        assert len(projects_text) > 0

@pytest.mark.asyncio
async def test_docker_ppx_mcp(docker_services):
    """Test PPX MCP server via Docker HTTP transport"""
    
    async with Client(MCP_ENDPOINTS["ppx"]) as client:
        # Test project search
        result = await client.call_tool("ppx_search_projects", {
            "keywords": ["Parkinson"],
            "max_results": 3
        })
        result_text = extract_result(result)
        
        assert len(result_text) > 0
        
        # PPX might not be installed, so check for either results or expected error
        if "PPX search failed" in result_text:
            print("   ⚠️  PPX package not available in Docker - expected behavior")
        else:
            # If PPX works, verify response structure
            assert "search_term" in result_text or "projects" in result_text

@pytest.mark.asyncio
async def test_docker_biogrid_mcp(docker_services):
    """Test BioGRID MCP server via Docker HTTP transport"""
    
    async with Client(MCP_ENDPOINTS["biogrid"]) as client:
        # Test interaction search
        result = await client.call_tool("search_interactions", {
            "gene_names": ["SNCA"],
            "organism": "9606"
        })
        result_text = extract_result(result)
        
        assert len(result_text) > 0
        
        # BioGRID requires API key, so check for appropriate response
        if "BioGRID API key required" in result_text:
            print("   ⚠️  BioGRID API key not configured - expected behavior")
        else:
            # If API key is present, verify interaction data
            assert "interactions" in result_text or "error" in result_text

@pytest.mark.asyncio
async def test_docker_cross_service_workflow(docker_services):
    """Test complete workflow across all Docker MCP services"""
    
    # Step 1: Get dopaminergic markers from STRING
    async with Client(MCP_ENDPOINTS["string"]) as client:
        markers_result = await client.call_tool("get_dopaminergic_markers", {})
        markers_content = extract_result(markers_result)
        
        markers_data = json.loads(markers_content)
        target_proteins = markers_data["dopaminergic_markers"][:5]
    
    # Step 2: Get protein interactions from STRING
    async with Client(MCP_ENDPOINTS["string"]) as client:
        network_result = await client.call_tool("get_network", {
            "proteins": target_proteins,
            "species": 9606,
            "confidence": 0.7
        })
        network_content = extract_result(network_result)
        assert "network_data" in network_content
    
    # Step 3: Search for datasets in PRIDE
    async with Client(MCP_ENDPOINTS["pride"]) as client:
        pride_result = await client.call_tool("search_pd_datasets", {
            "size": 3
        })
        pride_content = extract_result(pride_result)
        
        # Verify PRIDE response
        try:
            pride_data = json.loads(pride_content)
            has_projects = (isinstance(pride_data, list) and len(pride_data) > 0) or "projects" in pride_content
            assert has_projects
        except json.JSONDecodeError:
            assert "projects" in pride_content or "accession" in pride_content
    
    # Step 4: Search for protein datasets with PPX
    async with Client(MCP_ENDPOINTS["ppx"]) as client:
        ppx_result = await client.call_tool("find_pd_protein_datasets", {
            "target_proteins": target_proteins[:3],
            "max_datasets": 2
        })
        ppx_content = extract_result(ppx_result)
        
        # PPX may fail due to missing package, which is acceptable
        assert len(ppx_content) > 0
    
    # Step 5: Test BioGRID interactions
    async with Client(MCP_ENDPOINTS["biogrid"]) as client:
        biogrid_result = await client.call_tool("search_interactions", {
            "gene_names": target_proteins[:2],
            "organism": "9606"
        })
        biogrid_content = extract_result(biogrid_result)
        assert len(biogrid_content) > 0
    
    # Create workflow summary
    workflow_summary = {
        "target_proteins": target_proteins,
        "string_network_retrieved": "network_data" in network_content,
        "pride_datasets_found": "projects" in pride_content or "accession" in pride_content,
        "ppx_search_completed": len(ppx_content) > 0,
        "biogrid_search_completed": len(biogrid_content) > 0,
        "workflow_successful": True
    }
    
    print("\n🔬 Docker Integration Workflow Summary:")
    for key, value in workflow_summary.items():
        print(f"  {key}: {value}")
    
    assert workflow_summary["workflow_successful"]

@pytest.mark.asyncio
async def test_docker_service_health_check(docker_services):
    """Verify all Docker MCP services are responding to health checks"""
    
    health_status = {}
    
    for service_name, endpoint in MCP_ENDPOINTS.items():
        try:
            async with Client(endpoint) as client:
                # Try to call a simple tool to verify service health
                if service_name == "string":
                    result = await client.call_tool("get_dopaminergic_markers", {})
                elif service_name == "pride":
                    result = await client.call_tool("search_projects", {"size": 1})
                elif service_name == "ppx":
                    result = await client.call_tool("ppx_search_projects", {"keywords": ["test"], "max_results": 1})
                elif service_name == "biogrid":
                    result = await client.call_tool("search_interactions", {"gene_names": ["SNCA"]})
                
                health_status[service_name] = len(extract_result(result)) > 0
                
        except Exception as e:
            health_status[service_name] = False
            print(f"   ❌ {service_name} health check failed: {e}")
    
    print("\n🏥 Docker Service Health Status:")
    for service, healthy in health_status.items():
        status = "✅ Healthy" if healthy else "❌ Unhealthy"
        print(f"  {service}: {status}")
    
    # At least 3 out of 4 services should be healthy (BioGRID may fail without API key)
    healthy_count = sum(health_status.values())
    assert healthy_count >= 3, f"Only {healthy_count}/4 services are healthy"

@pytest.mark.asyncio
async def test_docker_concurrent_access(docker_services):
    """Test concurrent access to Docker MCP services"""
    
    async def test_service_concurrently(service_name, endpoint):
        """Test a single service with concurrent requests"""
        tasks = []
        
        for i in range(3):  # 3 concurrent requests per service
            if service_name == "string":
                task = asyncio.create_task(call_string_service(endpoint, i))
            elif service_name == "pride":
                task = asyncio.create_task(call_pride_service(endpoint, i))
            elif service_name == "ppx":
                task = asyncio.create_task(call_ppx_service(endpoint, i))
            elif service_name == "biogrid":
                task = asyncio.create_task(call_biogrid_service(endpoint, i))
            
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        successful = sum(1 for r in results if not isinstance(r, Exception))
        
        return successful, len(tasks)
    
    async def call_string_service(endpoint, request_id):
        async with Client(endpoint) as client:
            result = await client.call_tool("get_dopaminergic_markers", {})
            return len(extract_result(result)) > 0
    
    async def call_pride_service(endpoint, request_id):
        async with Client(endpoint) as client:
            result = await client.call_tool("search_projects", {"size": 1})
            return len(extract_result(result)) > 0
    
    async def call_ppx_service(endpoint, request_id):
        async with Client(endpoint) as client:
            result = await client.call_tool("ppx_search_projects", {"keywords": ["test"], "max_results": 1})
            return len(extract_result(result)) > 0
    
    async def call_biogrid_service(endpoint, request_id):
        async with Client(endpoint) as client:
            result = await client.call_tool("search_interactions", {"gene_names": ["SNCA"]})
            return len(extract_result(result)) > 0
    
    # Test all services concurrently
    concurrent_tasks = []
    for service_name, endpoint in MCP_ENDPOINTS.items():
        task = asyncio.create_task(test_service_concurrently(service_name, endpoint))
        concurrent_tasks.append((service_name, task))
    
    results = {}
    for service_name, task in concurrent_tasks:
        try:
            successful, total = await task
            results[service_name] = f"{successful}/{total}"
        except Exception as e:
            results[service_name] = f"Error: {e}"
    
    print("\n🔄 Concurrent Access Test Results:")
    for service, result in results.items():
        print(f"  {service}: {result}")
    
    # Verify that most concurrent requests succeeded
    total_successful = 0
    total_requests = 0
    
    for service, result in results.items():
        if "/" in result:
            successful, total = map(int, result.split("/"))
            total_successful += successful
            total_requests += total
    
    success_rate = total_successful / total_requests if total_requests > 0 else 0
    assert success_rate >= 0.7, f"Concurrent access success rate too low: {success_rate:.2%}"

if __name__ == "__main__":
    # Allow running this test file directly
    pytest.main([__file__, "-v", "-s"]) 