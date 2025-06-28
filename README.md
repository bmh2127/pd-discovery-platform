# Preclinical Neuroscience Discovery Platform

An AI-powered research platform that combines multi-agent AI systems with advanced data analysis capabilities to accelerate biomarker discovery and target identification in preclinical neuroscience research.

## 🔬 Overview

This platform leverages CrewAI's multi-agent framework to orchestrate comprehensive research workflows across multiple domains:
- **Academic Literature Discovery**: Systematic identification and validation of high-quality research papers
- **Code Implementation Mining**: Discovery and evaluation of relevant GitHub repositories and implementations
- **Educational Content Curation**: Compilation of learning resources and tutorial pathways
- **Knowledge Synthesis**: Integration of findings into actionable research strategies

## ✨ Key Features

### 🤖 Multi-Agent Research System
- **Academic Literature Specialist**: Discovers and validates systematic reviews, methodology papers, and high-impact publications
- **Code Implementation Hunter**: Finds and evaluates GitHub repositories with comprehensive technical validation
- **Educational Content Curator**: Curates learning resources with progressive difficulty assessment
- **Knowledge Synthesizer**: Integrates multi-source findings into strategic learning packages

### 📊 Advanced Data Analysis
- Differential expression analysis with volcano plots and heatmaps
- Principal Component Analysis (PCA) with score plots and scree plots
- Clinical correlation analysis for biomarker validation
- Statistical modeling and data visualization capabilities

### 🔍 Intelligent Research Tools
- **Serper API Integration**: Advanced web search with real URLs and content extraction
- **BrightData Web Scraping**: Robust content extraction from protected websites
- **Firecrawl Integration**: Enhanced web crawling capabilities
- **Quality Assessment Framework**: Rigorous validation of research resources

### 📈 Output Formats
- **JSON**: Structured data for programmatic access
- **Markdown**: Human-readable research reports
- **PDF**: Publication-ready research summaries
- **Excel**: Data analysis results and statistical outputs

## 🚀 Getting Started

### Prerequisites
- Python ≥ 3.12
- API Keys (see Configuration section)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd pd-discovery-platform
```

2. **Install dependencies**
```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -r requirements.txt
```

3. **Set up environment variables**
Create a `.env` file in the root directory:
```env
# OpenAI API Key for CrewAI agents
OPENAI_API_KEY=your_openai_api_key

# Serper API Key for web search
SERPER_API_KEY=your_serper_api_key

# Optional: Additional API keys for enhanced functionality
FIRECRAWL_API_KEY=your_firecrawl_api_key
BRIGHTDATA_API_KEY=your_brightdata_api_key
```

### Quick Start

Run a basic research query:
```bash
python -c "
from flow import PreclinicalResearchFlow
flow = PreclinicalResearchFlow('variational autoencoders for biomarker discovery')
result = flow.kickoff()
print(result)
"
```

Or use the main entry point:
```bash
python main.py
```

## 📋 Usage Examples

### Basic Research Workflow
```python
from flow import PreclinicalResearchFlow

# Initialize research flow
flow = PreclinicalResearchFlow(
    research_topic="protein-protein interaction networks in neurodegeneration",
    quality_threshold=4.0
)

# Execute complete research workflow
result = flow.kickoff()

# Results are automatically saved to research_results/
```

### Data Analysis Workflow
```python
from clinical_correlation import ClinicalCorrelationAnalyzer
from differential_expression import DifferentialExpressionAnalyzer

# Load and analyze data
analyzer = DifferentialExpressionAnalyzer()
results = analyzer.analyze_data("Data.xlsx")

# Generate visualizations
analyzer.create_volcano_plot()
analyzer.create_heatmap()
analyzer.perform_pca_analysis()
```

### Custom Agent Configuration
Modify `config/agents.yaml` and `config/tasks.yaml` to customize agent behavior and task definitions.

## 🏗️ Architecture

### Core Components

```
pd-discovery-platform/
├── flow.py                 # Main research workflow orchestration
├── crew.py                 # CrewAI agent and task definitions
├── state_management.py     # Data models and state management
├── parsing.py              # Research data parsing and validation
├── tools.py                # Web search and extraction tools
├── clinical_correlation.py # Clinical data analysis
├── main.py                 # Main entry point
├── test_ai_setup.py        # AI setup testing
├── config/                 # Agent and task configurations
│   ├── agents.yaml
│   └── tasks.yaml
├── MCP/                    # Model Context Protocol servers
│   ├── string-mcp/         # STRING database integration
│   ├── biogrid-mcp/        # BioGRID database integration  
│   ├── pride-mcp/          # PRIDE database integration
│   ├── tests/              # MCP-specific tests
│   └── docs/               # MCP documentation
├── tests/                  # Main test suite
├── research_results/       # Generated research reports
├── references/             # Reference papers and documentation
├── ScienceDirect_files_*/  # Downloaded research files
├── Data.xlsx               # Input datasets
├── differential_expression.xlsx # Analysis results
└── *.png                   # Generated visualization plots
```

### Data Flow

1. **Input**: Research topic specification
2. **Discovery**: Multi-agent parallel research across literature, code, and educational domains
3. **Validation**: Quality assessment and resource validation
4. **Synthesis**: Integration and prioritization of findings
5. **Output**: Comprehensive research reports and learning pathways

## 🛠️ Configuration

### Agent Customization
Edit `config/agents.yaml` to modify agent roles, goals, and expertise:
- **academic_literature_specialist**: Focus areas and search strategies
- **code_implementation_hunter**: Technical validation criteria
- **educational_content_curator**: Learning effectiveness assessment
- **knowledge_synthesizer_orchestrator**: Integration and prioritization logic

### Task Configuration
Modify `config/tasks.yaml` to adjust:
- Search strategies and quality criteria
- Output format specifications
- Validation requirements
- Integration parameters

### Quality Thresholds
Adjust quality assessment parameters in `flow.py`:
```python
flow = PreclinicalResearchFlow(
    research_topic="your_topic",
    quality_threshold=3.5,  # Minimum quality score (1-5)
)
```

## 📊 Data Analysis Capabilities

### Differential Expression Analysis
- Volcano plot generation
- Statistical significance testing
- Multiple comparison correction
- Heatmap visualization with hierarchical clustering

### Principal Component Analysis
- Dimensionality reduction
- Variance explanation analysis
- Score plot visualization
- Scree plot generation

### Clinical Correlation
- Biomarker-outcome correlation analysis
- Statistical modeling
- Clinical relevance assessment

## 🔧 Advanced Features

### Custom Search Tools
The platform includes specialized search tools:
- **Academic Search**: Focused on peer-reviewed publications
- **Code Search**: GitHub and repository discovery
- **Educational Search**: Tutorial and learning resource identification

### Quality Assessment Framework
Comprehensive evaluation criteria:
- **Academic Rigor**: Methodology and validation standards
- **Implementation Quality**: Code quality and documentation
- **Educational Value**: Learning effectiveness and clarity
- **Relevance Score**: Alignment with preclinical neuroscience

### Validation Pipeline
Multi-level validation process:
1. **Resource Quality**: Individual resource assessment
2. **Comprehensive Validation**: Cross-resource consistency
3. **Learning Path Validation**: Educational progression logic
4. **Final Report Generation**: Quality-assured outputs

## 🔗 Model Context Protocol (MCP) Servers

The platform integrates with specialized MCP servers for biological database access:

### Available MCP Servers
- **string-mcp**: Integration with STRING protein interaction database
  - Protein mapping and network analysis
  - Functional enrichment analysis
  - Dopaminergic pathway markers
  
- **biogrid-mcp**: BioGRID biological interaction database integration
  - Protein-protein interaction data
  - Genetic interaction networks
  - Publication-backed interaction evidence

- **pride-mcp**: PRIDE proteomics database integration
  - Mass spectrometry data access
  - Protein expression profiles
  - Proteomics experiment metadata

### Usage Example
```python
# Test MCP server functionality
cd MCP/tests
python test_string_mcp.py

# Use in research workflow
from MCP.string_mcp.server import map_proteins, get_network
proteins = ["SNCA", "PARK2", "TH"]  # Parkinson's disease markers
network = await get_network(proteins)
```

## 📈 Output Examples

### Research Report Structure
Generated reports include:
- **Executive Summary**: Key findings and recommendations
- **Resource Breakdown**: Categorized and scored resources
- **Quality Assessment**: Detailed evaluation metrics
- **Learning Pathways**: Structured educational progression
- **Implementation Guidance**: Practical next steps

### Analysis Outputs
- **Differential Expression Results**: `differential_expression.xlsx`
- **Visualization Files**: PNG plots and charts
- **Statistical Reports**: Comprehensive analysis summaries


## 📄 Dependencies

### Core Dependencies
- **CrewAI**: Multi-agent orchestration framework
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computing
- **Scikit-learn**: Machine learning algorithms
- **Matplotlib/Seaborn**: Data visualization
- **Pydantic**: Data validation and settings management
- **Pytest**: Testing framework for validation and QA
- **Jupyter**: Interactive analysis and experimentation

### API Dependencies
- **OpenAI**: LLM capabilities for agents
- **Serper**: Web search functionality
- **Firecrawl**: Web content extraction
- **BrightData**: Advanced web scraping

## 🔒 Security and Privacy

- API keys are managed through environment variables
- No sensitive data is logged or stored
- Web scraping respects robots.txt and rate limits
- All external API calls are properly authenticated

## 📚 Documentation

### Research Methodologies
The platform implements state-of-the-art research methodologies:
- Systematic literature review protocols
- Technical validation frameworks
- Educational effectiveness assessment
- Multi-source knowledge synthesis

### Quality Standards
All research outputs undergo rigorous quality assessment:
- Academic rigor evaluation
- Technical implementation validation
- Educational value assessment
- Relevance scoring for preclinical applications

## 🧪 Testing

### Running Tests
The platform includes comprehensive test suites for validation:

```bash
# Test AI setup and configuration
python test_ai_setup.py

# Run MCP server tests
cd MCP/tests
python -m pytest test_string_mcp.py -v

# Run all tests (if pytest is configured)
python -m pytest tests/ -v
```

### Test Coverage
- **AI Setup Tests**: Validate OpenAI API connectivity and model access
- **MCP Integration Tests**: Test protein database connectivity and data retrieval
- **Unit Tests**: Core functionality validation
- **Integration Tests**: End-to-end workflow testing

## 🆘 Troubleshooting

### Common Issues
1. **API Key Errors**: Ensure all required API keys are set in `.env`
2. **Import Errors**: Verify Python version (≥3.12) and dependencies
3. **Search Failures**: Check internet connection and API quotas
4. **Parsing Errors**: Review input data format and structure
5. **MCP Import Errors**: If you see `ModuleNotFoundError: No module named 'string_mcp'`, the import paths in tests have been fixed to use the correct directory structure

### Debug Mode
Enable verbose logging:
```python
flow = PreclinicalResearchFlow(
    research_topic="your_topic",
    quality_threshold=3.0
)
# Agents automatically run in verbose mode
```

## 📞 Support

For technical support, feature requests, or contributions:
- Create an issue in the repository
- Review existing documentation
- Check the troubleshooting section

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

*Built for advancing preclinical neuroscience research through AI-powered discovery and analysis.*