# MCP Servers for Parkinson's Disease Research

A suite of Model Context Protocol (MCP) servers providing integrated access to biological databases for Parkinson's disease research. This system enables cross-database protein analysis, interaction validation, and biomarker discovery workflows.

## 🏗️ Architecture Overview

### Active Services (4)
| Service | Port | Purpose | API Source |
|---------|------|---------|------------|
| **STRING MCP** | 8001 | Protein interaction networks | STRING Database API |
| **PRIDE MCP** | 8002 | Proteomics datasets | PRIDE Archive API |
| **BioGRID MCP** | 8003 | Validated protein interactions | BioGRID REST API |
| **Cross-Database MCP** | 8004 | Integration orchestrator | Aggregates above services |

### Key Features
- 🔄 **Real-time Integration**: Live API calls to authoritative databases
- 🔍 **Cross-Database Validation**: Convergent evidence identification
- 🧬 **Parkinson's Focus**: Curated biomarkers and research workflows
- 🐳 **Container Ready**: Docker Compose for easy deployment
- 🛡️ **Graceful Degradation**: Continues operation when individual services fail

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose (for containerized deployment)
- API keys for external services (see Configuration)

### Local Development Setup

1. **Clone and Setup Environment**
   ```bash
   git clone <repository>
   cd pd-discovery-platform/mcp_servers
   
   # Setup environment variables
   ./setup_env.sh local
   ```

2. **Install Dependencies**
   ```bash
   # Create virtual environment
   python -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows
   
   # Install for each service
   cd string_mcp && pip install -r requirements.txt && cd ..
   cd pride_mcp && pip install -r requirements.txt && cd ..
   cd biogrid_mcp && pip install -r requirements.txt && cd ..
   cd cross_database_mcp && pip install -r requirements.txt && cd ..
   ```

3. **Start Services** (in separate terminals)
   ```bash
   # Terminal 1: STRING MCP (Port 8001)
   cd string_mcp && python server.py
   
   # Terminal 2: PRIDE MCP (Port 8002)
   cd pride_mcp && python server.py
   
   # Terminal 3: BioGRID MCP (Port 8003)
   cd biogrid_mcp && python server.py
   
   # Terminal 4: Cross-Database MCP (Port 8004)
   cd cross_database_mcp && python server.py
   ```

### Docker Deployment

1. **Setup for Docker**
   ```bash
   ./setup_env.sh docker
   ```

2. **Start All Services**
   ```bash
   docker-compose up --build
   ```

3. **Verify Deployment**
   ```bash
   # Check all services are running
   curl http://localhost:8001/health  # STRING MCP
   curl http://localhost:8002/health  # PRIDE MCP
   curl http://localhost:8003/health  # BioGRID MCP
   curl http://localhost:8004/health  # Cross-Database MCP
   ```

## 🔧 Configuration

### Environment Variables

Create a `.env` file (or use `./setup_env.sh`):

```bash
# Service URLs (automatically configured by setup script)
STRING_MCP_URL=http://localhost:8001
PRIDE_MCP_URL=http://localhost:8002
BIOGRID_MCP_URL=http://localhost:8003

# API Keys (required for external services)
BIOGRID_API_KEY=your_biogrid_api_key_here
STRING_IDENTITY=your_string_identity_here

# Deployment mode
DOCKER_MODE=false
```

### API Keys Setup

1. **BioGRID API Key**: Get from [BioGRID](https://webservice.thebiogrid.org/)
2. **STRING Identity**: Register at [STRING-DB](https://string-db.org/cgi/access)

## 📊 API Usage Examples

### Cross-Database Protein Resolution
```bash
curl -X POST http://localhost:8004/call_tool \
  -H "Content-Type: application/json" \
  -d '{
    "name": "resolve_protein_entity",
    "arguments": {
      "identifier": "SNCA",
      "target_databases": ["string", "pride", "biogrid"]
    }
  }'
```

### Research Overview
```bash
curl "http://localhost:8004/read_resource?uri=research://parkinson/overview"
```

### Cross-Database Interaction Validation
```bash
curl -X POST http://localhost:8004/call_tool \
  -H "Content-Type: application/json" \
  -d '{
    "name": "cross_validate_interactions",
    "arguments": {
      "proteins": ["SNCA", "PARK2"],
      "databases": ["string", "biogrid"],
      "confidence_threshold": 0.4
    }
  }'
```

### Complete PD Workflow
```bash
curl -X POST http://localhost:8004/call_tool \
  -H "Content-Type: application/json" \
  -d '{
    "name": "execute_pd_workflow",
    "arguments": {
      "target_proteins": ["SNCA", "TH", "LRRK2"],
      "workflow_type": "biomarker_discovery"
    }
  }'
```

## 🧪 Testing

### Run All Tests
```bash
# Run tests for all services
python -m pytest tests/ -v

# Run specific service tests
python -m pytest tests/test_string_mcp.py -v
python -m pytest tests/test_pride_mcp.py -v
python -m pytest tests/test_biogrid_mcp.py -v
python -m pytest tests/test_cross_database_mcp.py -v

# Integration tests
python -m pytest tests/integration_test.py -v
```

### Docker Integration Tests
```bash
python -m pytest tests/test_docker_integration.py -v
```

## 📚 Individual Service Documentation

### STRING MCP (`string_mcp/`)
- **Purpose**: Protein-protein interaction networks
- **Key Tools**: `get_network`, `map_proteins`, `get_enrichment`
- **Resources**: Dopaminergic markers, PD pathways

### PRIDE MCP (`pride_mcp/`)
- **Purpose**: Proteomics datasets and experimental data
- **Key Tools**: `search_projects`, `get_project_files`, `search_peptides`
- **Resources**: Curated PD datasets, experimental protocols

### BioGRID MCP (`biogrid_mcp/`)
- **Purpose**: Validated protein interactions
- **Key Tools**: `search_interactions`, `get_organism_interactions`
- **Resources**: High-confidence interaction sets

### Cross-Database MCP (`cross_database_mcp/`)
- **Purpose**: Integration orchestrator and workflow engine
- **Key Tools**: `resolve_protein_entity`, `cross_validate_interactions`, `execute_pd_workflow`
- **Resources**: Research overviews, workflow templates

## 🎯 Use Cases

### 1. Biomarker Discovery
```bash
# Get research overview
curl "http://localhost:8004/read_resource?uri=research://parkinson/overview"

# Resolve candidate proteins across databases
curl -X POST http://localhost:8004/call_tool -d '{"name": "resolve_protein_entity", "arguments": {"identifier": "SNCA"}}'

# Execute discovery workflow
curl -X POST http://localhost:8004/call_tool -d '{"name": "execute_pd_workflow", "arguments": {"target_proteins": ["SNCA", "PARK2"], "workflow_type": "biomarker_discovery"}}'
```

### 2. Interaction Network Analysis
```bash
# Get STRING interaction network
curl -X POST http://localhost:8001/call_tool -d '{"name": "get_network", "arguments": {"proteins": ["SNCA", "TH"], "confidence": 700}}'

# Cross-validate with BioGRID
curl -X POST http://localhost:8004/call_tool -d '{"name": "cross_validate_interactions", "arguments": {"proteins": ["SNCA", "TH"], "databases": ["string", "biogrid"]}}'
```

### 3. Dataset Discovery
```bash
# Search PRIDE for relevant datasets
curl -X POST http://localhost:8002/call_tool -d '{"name": "search_projects", "arguments": {"query": "Parkinson", "size": 10}}'

# Get detailed project information
curl -X POST http://localhost:8002/call_tool -d '{"name": "get_project_details", "arguments": {"accession": "PXD015293"}}'
```

## 🏭 Production Considerations

### Scaling
- Services can be scaled independently using Docker Compose
- Consider load balancing for high-traffic scenarios
- Database connection pooling recommended for production

### Monitoring
- Health endpoints available for all services
- Structured logging throughout the system
- Metrics collection via standard MCP instrumentation

### Security
- API key rotation procedures
- Rate limiting on external API calls
- Input validation and sanitization

## 📈 Performance

### Typical Response Times
- Individual service calls: 100-500ms
- Cross-database operations: 1-3s
- Complete workflows: 5-15s

### Caching Strategy
- External API responses cached when appropriate
- Cross-database validation results cached temporarily
- Static resources (workflows, overviews) cached aggressively

## 🔄 Recent Changes

See [ARCHITECTURE_CLEANUP.md](../ARCHITECTURE_CLEANUP.md) for details on recent architectural improvements:

- ✅ Removed redundant PPX MCP service
- ✅ Eliminated static resource duplication
- ✅ Streamlined port assignments (8001-8004)
- ✅ Improved real-time integration patterns

## 🤝 Contributing

### Development Workflow
1. Create feature branch
2. Update relevant service(s)
3. Add/update tests
4. Update documentation
5. Test locally and with Docker
6. Submit pull request

### Adding New Services
1. Follow existing service patterns (FastMCP framework)
2. Add Docker configuration
3. Update docker-compose.yml
4. Add environment variables to setup_env.sh
5. Create comprehensive tests
6. Update this README

### Integration Guidelines
- Use HTTP for inter-service communication
- Implement graceful degradation for service unavailability
- Follow the principle: "Resources for unique value, Tools for operations"
- Maintain single source of truth for each data type

## 📞 Support

- **Issues**: GitHub Issues
- **Documentation**: Individual service README files
- **Architecture**: See ARCHITECTURE_CLEANUP.md
- **Examples**: See tests/ directory for usage patterns

## 📄 License

[Your License Here]

---

**Built with ❤️ for Parkinson's Disease Research**
