# Cross-Database MCP Server

The Cross-Database MCP server provides true cross-database integration by orchestrating HTTP calls to other MCP services in real-time. This enables dynamic protein resolution, interaction validation, and research overview aggregation across multiple biological databases.

## Architecture Philosophy

**Focus on Real-Time Integration**: Rather than duplicating data in static resources, this server acts as an intelligent orchestrator that makes live API calls to other MCP services and provides cross-database synthesis and validation.

**Resources for Unique Value Only**:
- Research context and curation (domain expertise)
- Workflow templates and methodologies  
- Cross-database aggregated views not available elsewhere

**Tools for Dynamic Operations**:
- Real-time protein resolution across databases
- Live interaction validation and cross-referencing
- Dynamic workflow execution

## Features

- **Real-time Integration**: Makes live HTTP calls to STRING, PRIDE, and BioGRID MCP servers
- **Environment-Adaptive**: Supports both local development and Docker deployment configurations
- **Fallback Resilience**: Gracefully handles service unavailability with fallback data
- **Cross-Validation**: Identifies convergent evidence across multiple databases
- **No Data Duplication**: Eliminates redundancy by using tools for dynamic data instead of static resources

## Environment Configuration

The server uses environment variables to configure service URLs:

### Local Development
```bash
STRING_MCP_URL=http://localhost:8001
PRIDE_MCP_URL=http://localhost:8002
BIOGRID_MCP_URL=http://localhost:8003
```

### Docker Deployment
```bash
STRING_MCP_URL=http://string_mcp:8000
PRIDE_MCP_URL=http://pride_mcp:8000
BIOGRID_MCP_URL=http://biogrid_mcp:8000
```

## Setup

1. **Environment Setup**: Use the provided setup script
   ```bash
   # For local development
   ./setup_env.sh local
   
   # For Docker deployment
   ./setup_env.sh docker
   ```

2. **Local Development**: Start individual MCP servers on their configured ports
   ```bash
   # Start each MCP server in separate terminals
   cd string_mcp && python server.py     # Port 8001
   cd pride_mcp && python server.py      # Port 8002  
   cd biogrid_mcp && python server.py    # Port 8003
   cd cross_database_mcp && python server.py  # Port 8004
   ```

3. **Docker Deployment**: Use Docker Compose
   ```bash
   docker-compose up --build
   ```

## API Functions (Real-Time Tools)

### resolve_protein_entity
Resolves a protein identifier across multiple databases using real-time API calls. **This replaces static protein resources** with dynamic, always-current data.

**Parameters:**
- `identifier`: Protein symbol or ID (e.g., "SNCA")
- `target_databases`: List of databases to query (default: ["string", "pride", "biogrid"])

**Returns:** Cross-database mapping with confidence scores and status

**Example:**
```json
{
  "query": "SNCA",
  "status": "resolved",
  "database_mappings": {
    "string": {"id": "9606.ENSP00000338345", "name": "SNCA"},
    "pride": {"dataset_count": 3},
    "biogrid": {"interaction_count": 156}
  },
  "overall_confidence": 0.85
}
```

### cross_validate_interactions
Validates protein interactions across STRING and BioGRID using live data.

**Parameters:**
- `proteins`: List of protein identifiers
- `databases`: Databases to query (default: ["string", "biogrid"])
- `confidence_threshold`: Minimum confidence level (0-1)

**Returns:** Interaction validation with convergent evidence analysis

### execute_pd_workflow
Executes a complete Parkinson's disease research workflow using real-time data.

**Parameters:**
- `target_proteins`: List of proteins to analyze
- `workflow_type`: Type of analysis ("biomarker_discovery", "pathway_analysis", "clinical_translation")

**Returns:** Comprehensive workflow results with cross-database integration

## Resources (Unique Value Only)

### research://parkinson/overview
Provides curated research context and live dataset aggregation. **This provides unique value** not available from individual services.

**Content:**
- Curated biomarker classifications (established vs emerging)
- Live dataset counts from PRIDE MCP
- Research workflow guidance
- Key pathway context

### workflow://pd-biomarker-discovery
Methodology template for systematic biomarker discovery. **Pure value-add** that orchestrates the real-time tools.

**Content:**
- Step-by-step research methodology
- Tool usage guidance
- Confidence thresholds
- Best practices

## Architecture Benefits

1. **No Data Duplication**: Eliminates redundant static data that duplicates what tools can provide dynamically
2. **Always Current**: Real-time API calls ensure data is never stale
3. **Single Source of Truth**: Each database service remains the authoritative source
4. **Focused Resources**: Resources only provide unique value (curation, context, workflows)
5. **Better Performance**: No need to maintain static copies of dynamic data

## Error Handling

The server implements robust error handling:
- **Service Unavailability**: Falls back to curated data when services are unreachable
- **Timeout Handling**: 30-60 second timeouts for API calls
- **Graceful Degradation**: Continues operation even if some services fail
- **Error Reporting**: Detailed error messages in response data

## Testing

Tests are designed to handle both successful service integration and service unavailability scenarios:

```bash
pytest tests/test_cross_database_mcp.py -v
```

## Dependencies

- `fastmcp>=0.1.0`: MCP server framework
- `httpx>=0.25.0`: Async HTTP client for service communication
- `pydantic>=2.0.0`: Data validation and serialization
