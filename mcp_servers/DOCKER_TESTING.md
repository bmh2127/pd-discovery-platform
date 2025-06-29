# Docker Integration Testing Guide

This guide explains how to test the MCP servers running in Docker containers via HTTP transport.

## Overview

The `test_docker_integration.py` file provides comprehensive testing for all MCP servers when deployed as Docker containers. Unlike the regular integration tests that use stdio transport, these tests use HTTP transport to communicate with containerized services.

## Test Structure

### 📁 Files
- `tests/test_docker_integration.py` - Main Docker integration test suite
- `docker-compose.yml` - Docker services configuration
- Individual `dockerfile` files for each MCP server

### 🔧 Test Functions

1. **Individual Service Tests**
   - `test_docker_string_mcp()` - Tests STRING MCP server
   - `test_docker_pride_mcp()` - Tests PRIDE MCP server  
   - `test_docker_ppx_mcp()` - Tests PPX MCP server
   - `test_docker_biogrid_mcp()` - Tests BioGRID MCP server

2. **Integration Tests**
   - `test_docker_cross_service_workflow()` - Tests complete workflow across all services
   - `test_docker_service_health_check()` - Verifies all services are healthy
   - `test_docker_concurrent_access()` - Tests concurrent access to services

## Running the Tests

### Prerequisites
- Docker and Docker Compose installed
- Python dependencies: `pytest`, `fastmcp`, `asyncio`

### Quick Start
```bash
# Run all Docker integration tests
python -m pytest tests/test_docker_integration.py -v -s

# Run specific test
python -m pytest tests/test_docker_integration.py::test_docker_service_health_check -v -s

# Run with extra verbosity
python -m pytest tests/test_docker_integration.py -v -s --tb=short
```

### Test Isolation
Each test automatically:
1. 🐳 Starts Docker services with `docker-compose up -d --build`
2. ⏳ Waits 10 seconds for services to initialize
3. 🧪 Runs the test
4. 🧹 Cleans up with `docker-compose down`

## Service Endpoints

The tests connect to these HTTP endpoints:
- **STRING MCP**: `http://localhost:8001/mcp/`
- **PRIDE MCP**: `http://localhost:8002/mcp/`
- **PPX MCP**: `http://localhost:8003/mcp/`
- **BioGRID MCP**: `http://localhost:8004/mcp/`

## Expected Behavior

### ✅ Successful Tests
- All services should start and respond to health checks
- STRING and PRIDE APIs should return valid data
- PPX may show "package not available" errors (expected)
- BioGRID may show "API key required" errors (expected without key)

### ⚠️ Expected Warnings
```
⚠️ PPX package not available in Docker - expected behavior
⚠️ BioGRID API key not configured - expected behavior
```

### 🔄 Concurrent Access Testing
The concurrent access test validates that services can handle multiple simultaneous requests:
- 3 concurrent requests per service
- Minimum 70% success rate required
- Tests service stability under load

## Troubleshooting

### Docker Issues
```bash
# Check Docker service status
docker-compose ps

# View service logs
docker-compose logs

# Force rebuild
docker-compose up -d --build --force-recreate
```

### Port Conflicts
If ports 8001-8004 are in use:
```bash
# Check what's using the ports
sudo lsof -i :8001-8004

# Stop conflicting services
docker-compose down
```

### Test Failures
```bash
# Run single test with detailed output
python -m pytest tests/test_docker_integration.py::test_docker_service_health_check -v -s --tb=long

# Check Docker logs for specific service
docker-compose logs string_mcp
```

## Comparison with Regular Tests

| Test Type | Transport | Use Case |
|-----------|-----------|----------|
| **Regular Tests** (`integration_test.py`) | stdio | Local development, debugging |
| **Docker Tests** (`test_docker_integration.py`) | HTTP | Production deployment, CI/CD |

## Environment Variables

### Optional Configuration
- `BIOGRID_API_KEY` - Enables full BioGRID functionality
- `DOCKER_MODE=true` - Automatically set in Docker containers

### Docker Compose Environment
```yaml
environment:
  - BIOGRID_API_KEY=${BIOGRID_API_KEY}
  - DOCKER_MODE=true
```

## Best Practices

1. **Always run with `-s` flag** to see Docker startup messages
2. **Use specific test names** when debugging individual services
3. **Check Docker logs** if tests fail unexpectedly
4. **Allow 10+ seconds** for Docker services to start
5. **Clean up manually** if tests are interrupted: `docker-compose down`

## Integration Example

```python
# Example from test_docker_cross_service_workflow()
async def test_workflow():
    # 1. Get markers from STRING
    async with Client("http://localhost:8001/mcp/") as client:
        markers = await client.call_tool("get_dopaminergic_markers", {})
    
    # 2. Get interactions from STRING  
    async with Client("http://localhost:8001/mcp/") as client:
        network = await client.call_tool("get_network", {"proteins": ["SNCA"]})
    
    # 3. Search datasets in PRIDE
    async with Client("http://localhost:8002/mcp/") as client:
        datasets = await client.call_tool("search_pd_datasets", {"size": 5})
```

This demonstrates the complete preclinical neuroscience research workflow using Docker-deployed MCP servers! 🧬🔬 