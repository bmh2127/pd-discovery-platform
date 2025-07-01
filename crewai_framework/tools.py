# tools.py
"""
CrewAI Tools for PD Discovery Platform - Systematic Parkinson's Disease Research
Tools for challenging the α-synuclein paradigm through cross-database molecular discovery
"""

import json
import asyncio
import httpx
from typing import List, Dict, Any
from crewai.tools import tool
from pydantic import BaseModel, Field

# ================================
# TOOL INPUT SCHEMAS
# ================================

class DopaminergicNetworkInput(BaseModel):
    """Input schema for dopaminergic network building"""
    discovery_mode: str = Field(
        default="comprehensive",
        description="Discovery mode: 'minimal', 'standard', 'comprehensive', or 'hypothesis_free'"
    )
    confidence_threshold: float = Field(
        default=0.7,
        description="Minimum confidence for interactions (0.0-1.0)",
        ge=0.0,
        le=1.0
    )
    include_indirect: bool = Field(
        default=True,
        description="Include PD-associated proteins with dopaminergic effects"
    )
    max_white_nodes: int = Field(
        default=20,
        description="Maximum number of novel proteins to discover",
        ge=0,
        le=100
    )

class CrossValidationInput(BaseModel):
    """Input schema for cross-database validation"""
    proteins: List[str] = Field(
        description="List of protein identifiers to analyze"
    )
    databases: List[str] = Field(
        default=["string", "biogrid"],
        description="Databases to cross-validate against"
    )
    confidence_threshold: float = Field(
        default=0.4,
        description="Minimum confidence for interactions",
        ge=0.0,
        le=1.0
    )

class BatchResolveInput(BaseModel):
    """Input schema for batch protein resolution"""
    identifiers: List[str] = Field(
        description="List of protein identifiers to resolve"
    )
    target_databases: List[str] = Field(
        default=["string", "pride", "biogrid"],
        description="Target databases for resolution"
    )

class PDWorkflowInput(BaseModel):
    """Input schema for PD workflow execution"""
    target_proteins: List[str] = Field(
        default=["SNCA", "PRKN", "TH"],
        description="Proteins to analyze (defaults to key PD proteins)"
    )
    workflow_type: str = Field(
        default="biomarker_discovery",
        description="Type of workflow to execute"
    )

# ================================
# MCP COMMUNICATION UTILITIES
# ================================

async def call_mcp_tool_async(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Asynchronously call MCP tool via HTTP and return result
    
    Args:
        tool_name: Name of the MCP tool to call
        arguments: Arguments to pass to the tool
        
    Returns:
        Dictionary containing the tool result
        
    Raises:
        Exception: If MCP call fails
    """
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "http://localhost:8000/call_tool",
                json={"name": tool_name, "arguments": arguments}
            )
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException:
        raise Exception(f"MCP tool {tool_name} timed out after 120 seconds")
    except httpx.HTTPStatusError as e:
        raise Exception(f"MCP tool {tool_name} failed with HTTP {e.response.status_code}: {e.response.text}")
    except Exception as e:
        raise Exception(f"MCP tool {tool_name} failed: {str(e)}")

def call_mcp_tool_sync(tool_name: str, arguments: Dict[str, Any]) -> str:
    """
    Synchronously call MCP tool (for CrewAI compatibility)
    
    Args:
        tool_name: Name of the MCP tool to call
        arguments: Arguments to pass to the tool
        
    Returns:
        JSON string containing the tool result
    """
    try:
        # Get or create event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Run async call
        if loop.is_running():
            # If loop is already running, we need to use a different approach
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, call_mcp_tool_async(tool_name, arguments))
                result = future.result(timeout=120)
        else:
            result = loop.run_until_complete(call_mcp_tool_async(tool_name, arguments))
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_result = {
            "error": str(e),
            "tool_name": tool_name,
            "arguments": arguments,
            "status": "failed"
        }
        return json.dumps(error_result, indent=2)

async def read_mcp_resource_async(resource_uri: str) -> str:
    """
    Asynchronously read MCP resource via HTTP
    
    Args:
        resource_uri: URI of the resource to read
        
    Returns:
        String content of the resource
        
    Raises:
        Exception: If resource read fails
    """
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(
                "http://localhost:8000/read_resource",
                params={"uri": resource_uri}
            )
            response.raise_for_status()
            data = response.json()
            
            # Extract text content from MCP resource response
            if isinstance(data, list) and len(data) > 0:
                return data[0].get("text", str(data))
            return str(data)
    except Exception as e:
        raise Exception(f"Failed to read MCP resource {resource_uri}: {str(e)}")

def read_mcp_resource_sync(resource_uri: str) -> str:
    """
    Synchronously read MCP resource (for CrewAI compatibility)
    
    Args:
        resource_uri: URI of the resource to read
        
    Returns:
        String content of the resource
    """
    try:
        # Get or create event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Run async call
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, read_mcp_resource_async(resource_uri))
                result = future.result(timeout=60)
        else:
            result = loop.run_until_complete(read_mcp_resource_async(resource_uri))
        
        return result
        
    except Exception as e:
        return f"Error reading MCP resource {resource_uri}: {str(e)}"

# ================================
# CREWAI TOOLS IMPLEMENTATION
# ================================

@tool("Build Dopaminergic Network")
def build_dopaminergic_network_tool(
    discovery_mode: str = "comprehensive",
    confidence_threshold: float = 0.7,
    include_indirect: bool = True,
    max_white_nodes: int = 20
) -> str:
    """
    Build comprehensive dopaminergic reference network for systematic discovery.
    
    This tool enables paradigm-challenging research by systematically mapping
    the complete dopaminergic interaction network and identifying unexpected
    connections that may reveal early disruption patterns in Parkinson's disease.
    
    The tool constructs networks using multiple discovery modes:
    - 'minimal': Core dopaminergic proteins only (TH, DDC, VMAT2, DAT)
    - 'standard': Core proteins plus direct interactors
    - 'comprehensive': Extended network including PD-associated proteins
    - 'hypothesis_free': Broadest discovery without preconceptions
    
    Key paradigm-challenging features:
    - Identifies unexpected connections between pathology and synthesis proteins
    - Discovers novel proteins through white node analysis
    - Analyzes network topology for hub proteins and functional clusters
    - Provides quantitative evidence for early dopaminergic disruption
    
    Args:
        discovery_mode: Discovery breadth ("minimal", "standard", "comprehensive", "hypothesis_free")
        confidence_threshold: Minimum confidence for interactions (0.0-1.0)
        include_indirect: Include PD-associated proteins with dopaminergic effects
        max_white_nodes: Maximum number of novel proteins to discover
    
    Returns:
        JSON string with comprehensive network analysis including:
        - Complete interaction network with confidence scores
        - Novel protein discoveries and unexpected connections
        - Functional clustering analysis (synthesis, transport, receptors, pathology)
        - Paradigm-challenging evidence and validation recommendations
        - Network topology metrics and hub protein identification
    """
    
    # Validate inputs
    valid_modes = ["minimal", "standard", "comprehensive", "hypothesis_free"]
    if discovery_mode not in valid_modes:
        return json.dumps({
            "error": f"Invalid discovery_mode '{discovery_mode}'. Must be one of: {valid_modes}",
            "status": "failed"
        })
    
    if not 0.0 <= confidence_threshold <= 1.0:
        return json.dumps({
            "error": f"confidence_threshold must be between 0.0 and 1.0, got {confidence_threshold}",
            "status": "failed"
        })
    
    arguments = {
        "discovery_mode": discovery_mode,
        "confidence_threshold": confidence_threshold,
        "include_indirect": include_indirect,
        "max_white_nodes": max_white_nodes
    }
    
    print(f"🔬 Building dopaminergic network with mode: {discovery_mode}, threshold: {confidence_threshold}")
    result = call_mcp_tool_sync("build_dopaminergic_reference_network_tool", arguments)
    
    try:
        # Parse and enhance result for paradigm challenge research
        result_data = json.loads(result)
        if "error" not in result_data:
            print(f"✅ Network built successfully: {result_data.get('network_construction', {}).get('total_core_proteins', 'Unknown')} proteins")
        return result
    except json.JSONDecodeError:
        return json.dumps({
            "error": "Failed to parse network building result",
            "raw_result": result,
            "status": "failed"
        })

@tool("Cross Validate Protein Interactions") 
def cross_validate_interactions_tool(
    proteins: List[str],
    databases: List[str] = None,
    confidence_threshold: float = 0.4
) -> str:
    """
    Cross-validate protein interactions across multiple databases for research confidence.
    
    Essential for paradigm-challenging research - identifies interactions with convergent
    evidence across STRING and BioGRID databases. This validation provides the scientific
    rigor needed to challenge established paradigms by ensuring discoveries are supported
    by multiple independent data sources.
    
    The tool performs comprehensive cross-database validation by:
    - Resolving protein identifiers across different naming conventions
    - Identifying interactions confirmed in multiple databases
    - Calculating consensus confidence scores
    - Prioritizing interactions with strongest evidence
    - Highlighting paradigm-challenging connections for experimental validation
    
    Validation is critical for paradigm-challenging research because:
    - Establishes scientific credibility for controversial findings
    - Reduces false discovery rates in network analysis
    - Provides quantitative evidence strength metrics
    - Identifies the most reliable targets for experimental validation
    
    Args:
        proteins: List of protein identifiers to analyze (gene symbols preferred)
        databases: Databases to cross-validate against (default: ["string", "biogrid"])
        confidence_threshold: Minimum confidence for interactions (0.0-1.0)
    
    Returns:
        JSON string with cross-validation results including:
        - Cross-validated interactions with consensus confidence scores
        - Database coverage and resolution success rates
        - Convergent evidence summary with supporting databases
        - Priority interactions for experimental validation
        - Validation confidence assessment for research credibility
    """
    
    if databases is None:
        databases = ["string", "biogrid"]
    
    # Validate inputs
    if not proteins:
        return json.dumps({
            "error": "proteins list cannot be empty",
            "status": "failed"
        })
    
    if not 0.0 <= confidence_threshold <= 1.0:
        return json.dumps({
            "error": f"confidence_threshold must be between 0.0 and 1.0, got {confidence_threshold}",
            "status": "failed"
        })
    
    valid_databases = ["string", "biogrid", "pride"]
    invalid_dbs = [db for db in databases if db not in valid_databases]
    if invalid_dbs:
        return json.dumps({
            "error": f"Invalid databases: {invalid_dbs}. Valid options: {valid_databases}",
            "status": "failed"
        })
    
    arguments = {
        "proteins": proteins,
        "databases": databases,
        "confidence_threshold": confidence_threshold
    }
    
    print(f"🔍 Cross-validating {len(proteins)} proteins across {len(databases)} databases")
    print(f"   Proteins: {', '.join(proteins[:5])}{'...' if len(proteins) > 5 else ''}")
    print(f"   Databases: {', '.join(databases)}")
    
    result = call_mcp_tool_sync("cross_validate_interactions", arguments)
    
    try:
        # Parse and enhance result 
        result_data = json.loads(result)
        if "error" not in result_data:
            validated_count = result_data.get("validation_summary", {}).get("cross_validated_interactions", 0)
            total_count = result_data.get("validation_summary", {}).get("total_interactions_found", 0)
            print(f"✅ Cross-validation complete: {validated_count}/{total_count} interactions validated")
        return result
    except json.JSONDecodeError:
        return json.dumps({
            "error": "Failed to parse cross-validation result",
            "raw_result": result,
            "status": "failed"
        })

@tool("Batch Resolve Proteins")
def batch_resolve_proteins_tool(
    identifiers: List[str],
    target_databases: List[str] = None
) -> str:
    """
    Efficiently resolve multiple proteins across databases simultaneously.
    
    Optimized for systematic discovery workflows requiring analysis of multiple
    protein entities with cross-database validation. This tool ensures consistent
    protein identification across different databases that may use different
    naming conventions, aliases, or identifier systems.
    
    The tool provides comprehensive protein entity resolution by:
    - Mapping gene symbols to canonical identifiers
    - Resolving protein aliases and alternative names
    - Checking availability across target databases
    - Providing confidence scores for entity resolution
    - Identifying proteins that may require manual curation
    
    Batch processing is essential for paradigm-challenging research because:
    - Enables systematic analysis of large protein sets
    - Ensures consistent protein identification across workflows
    - Reduces API call overhead for large-scale studies
    - Provides standardized protein references for cross-database analysis
    - Identifies potential data gaps that could affect research conclusions
    
    Args:
        identifiers: List of protein identifiers to resolve (gene symbols, UniProt IDs, etc.)
        target_databases: Target databases for resolution (default: ["string", "pride", "biogrid"])
        
    Returns:
        JSON string with batch resolution results including:
        - Resolved protein entities with canonical identifiers
        - Database availability and coverage statistics
        - Resolution confidence scores and success rates
        - Unresolved identifiers requiring manual curation
        - Standardized protein references for downstream analysis
    """
    
    if target_databases is None:
        target_databases = ["string", "pride", "biogrid"]
    
    # Validate inputs
    if not identifiers:
        return json.dumps({
            "error": "identifiers list cannot be empty",
            "status": "failed"
        })
    
    valid_databases = ["string", "pride", "biogrid"]
    invalid_dbs = [db for db in target_databases if db not in valid_databases]
    if invalid_dbs:
        return json.dumps({
            "error": f"Invalid target_databases: {invalid_dbs}. Valid options: {valid_databases}",
            "status": "failed"
        })
    
    arguments = {
        "identifiers": identifiers,
        "target_databases": target_databases
    }
    
    print(f"🔤 Batch resolving {len(identifiers)} protein identifiers")
    print(f"   Identifiers: {', '.join(identifiers[:5])}{'...' if len(identifiers) > 5 else ''}")
    print(f"   Target databases: {', '.join(target_databases)}")
    
    result = call_mcp_tool_sync("batch_resolve_proteins", arguments)
    
    try:
        # Parse and enhance result
        result_data = json.loads(result)
        if "error" not in result_data:
            resolved_count = result_data.get("resolution_summary", {}).get("successfully_resolved", 0)
            total_count = len(identifiers)
            success_rate = (resolved_count / total_count * 100) if total_count > 0 else 0
            print(f"✅ Batch resolution complete: {resolved_count}/{total_count} proteins resolved ({success_rate:.1f}%)")
        return result
    except json.JSONDecodeError:
        return json.dumps({
            "error": "Failed to parse batch resolution result", 
            "raw_result": result,
            "status": "failed"
        })

@tool("Get Research Overview")
def get_research_overview_tool() -> str:
    """
    Get comprehensive Parkinson's disease research overview and paradigm context.
    
    Provides established and emerging biomarkers, available datasets, research workflows,
    and database coverage for systematic discovery. This overview is essential for
    paradigm-challenging research as it establishes the current scientific landscape
    and identifies opportunities for challenging established assumptions.
    
    The research overview includes:
    - Current α-synuclein-centric paradigm description and limitations
    - Established dopaminergic biomarkers and their clinical context
    - Available molecular datasets and their research applications
    - Cross-database coverage and data quality assessments
    - Research gaps and opportunities for paradigm-shifting discoveries
    
    This tool is critical for paradigm-challenging research because:
    - Establishes baseline understanding of current paradigms
    - Identifies specific assumptions that can be challenged
    - Provides context for interpreting novel molecular discoveries
    - Guides hypothesis generation for paradigm-shifting research
    - Ensures research builds appropriately on existing knowledge
    
    Returns:
        Comprehensive research overview including:
        - Current Parkinson's disease research paradigms and their limitations
        - Established and emerging biomarkers with clinical validation status
        - Available molecular datasets and database coverage
        - Research workflows and methodological approaches
        - Identified gaps and opportunities for paradigm-challenging research
        - Historical context of paradigm shifts in Parkinson's disease research
    """
    
    print("📚 Retrieving comprehensive PD research overview...")
    
    try:
        # Read research overview from MCP resource
        result = read_mcp_resource_sync("research://parkinson/overview")
        
        # Validate that we got content
        if result.startswith("Error reading"):
            return json.dumps({
                "error": "Failed to retrieve research overview",
                "details": result,
                "status": "failed"
            })
        
        print("✅ Research overview retrieved successfully")
        
        # Structure the response for better usability
        return json.dumps({
            "status": "success",
            "research_overview": result,
            "overview_type": "comprehensive_pd_research_landscape",
            "paradigm_focus": "alpha_synuclein_centric_vs_dopaminergic_disruption",
            "timestamp": "current",
            "content_length": len(result),
            "usage_note": "Use this overview to understand current paradigms and identify challenge opportunities"
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"Failed to retrieve research overview: {str(e)}",
            "status": "failed"
        })

@tool("Execute PD Workflow")
def execute_pd_workflow_tool(
    target_proteins: List[str] = None,
    workflow_type: str = "biomarker_discovery"
) -> str:
    """
    Execute complete Parkinson's disease research workflow for paradigm challenge.
    
    Orchestrates multi-step discovery process including protein resolution, interaction
    validation, and systematic analysis for paradigm-challenging insights. This workflow
    is specifically designed to challenge the α-synuclein-centric paradigm by systematically
    analyzing dopaminergic network disruptions and their temporal relationships.
    
    The workflow executes comprehensive analysis including:
    - Systematic protein resolution and standardization
    - Cross-database interaction validation for research confidence
    - Network topology analysis to identify hub proteins and clusters
    - Paradigm challenge assessment through temporal disruption analysis
    - Biomarker prioritization based on paradigm-shifting potential
    - Experimental validation recommendations for challenging findings
    
    Workflow types supported:
    - 'biomarker_discovery': Focus on biomarker identification and validation
    - 'network_analysis': Comprehensive network topology and interaction analysis
    - 'paradigm_challenge': Systematic paradigm challenge through molecular evidence
    - 'temporal_analysis': Temporal sequence analysis of molecular disruptions
    - 'therapeutic_discovery': Target identification for therapeutic development
    
    This comprehensive workflow is essential for paradigm-challenging research because:
    - Provides systematic approach to challenging established scientific assumptions
    - Ensures research rigor through multi-database validation
    - Generates quantitative evidence for alternative disease mechanisms
    - Identifies specific experimental validations needed for paradigm shifts
    - Bridges computational discovery with experimental research priorities
    
    Args:
        target_proteins: Proteins to analyze (defaults to key PD proteins: SNCA, PRKN, TH)
        workflow_type: Type of workflow to execute (default: "biomarker_discovery")
        
    Returns:
        JSON string with complete workflow results including:
        - Systematic protein resolution and standardization results
        - Cross-database validation summary with confidence metrics
        - Network analysis results with paradigm-challenging insights
        - Biomarker prioritization with experimental validation recommendations
        - Research confidence assessment and next steps for paradigm challenge
        - Comprehensive result summary with actionable research priorities
    """
    
    if target_proteins is None:
        target_proteins = ["SNCA", "PRKN", "TH"]
    
    # Validate inputs
    valid_workflows = [
        "biomarker_discovery", 
        "network_analysis", 
        "paradigm_challenge", 
        "temporal_analysis", 
        "therapeutic_discovery"
    ]
    
    if workflow_type not in valid_workflows:
        return json.dumps({
            "error": f"Invalid workflow_type '{workflow_type}'. Valid options: {valid_workflows}",
            "status": "failed"
        })
    
    if not target_proteins:
        return json.dumps({
            "error": "target_proteins list cannot be empty",
            "status": "failed"
        })
    
    arguments = {
        "target_proteins": target_proteins,
        "workflow_type": workflow_type
    }
    
    print(f"🔬 Executing PD workflow: {workflow_type}")
    print(f"   Target proteins: {', '.join(target_proteins)}")
    print(f"   Workflow type: {workflow_type}")
    
    result = call_mcp_tool_sync("execute_pd_workflow", arguments)
    
    try:
        # Parse and enhance result
        result_data = json.loads(result)
        if "error" not in result_data:
            workflow_status = result_data.get("workflow_status", "unknown")
            print(f"✅ PD workflow completed with status: {workflow_status}")
            
            # Add workflow metadata for better usability
            result_data["workflow_metadata"] = {
                "workflow_type": workflow_type,
                "target_proteins": target_proteins,
                "execution_timestamp": "current",
                "paradigm_focus": "dopaminergic_disruption_vs_alpha_synuclein",
                "research_approach": "systematic_paradigm_challenge"
            }
            
            return json.dumps(result_data, indent=2)
        else:
            print(f"❌ Workflow failed: {result_data.get('error', 'Unknown error')}")
            return result
    except json.JSONDecodeError:
        return json.dumps({
            "error": "Failed to parse PD workflow result",
            "raw_result": result,
            "status": "failed"
        })

# ================================
# TOOL VALIDATION AND TESTING
# ================================

def validate_mcp_connection() -> bool:
    """
    Validate that MCP server is accessible and responsive
    
    Returns:
        True if MCP server is accessible, False otherwise
    """
    try:
        import httpx
        response = httpx.get("http://localhost:8000/health", timeout=10.0)
        return response.status_code == 200
    except Exception:
        return False

def test_all_tools() -> Dict[str, bool]:
    """
    Test all tools with minimal inputs to verify functionality
    
    Returns:
        Dictionary with tool names and their test results
    """
    results = {}
    
    print("🧪 Testing all PD Discovery Platform tools...")
    
    # Test MCP connection first
    mcp_connected = validate_mcp_connection()
    results["mcp_connection"] = mcp_connected
    
    if not mcp_connected:
        print("❌ MCP server not accessible - skipping tool tests")
        return results
    
    # Test build_dopaminergic_network_tool
    try:
        result = build_dopaminergic_network_tool(
            discovery_mode="minimal",
            confidence_threshold=0.7,
            max_white_nodes=5
        )
        data = json.loads(result)
        results["build_dopaminergic_network_tool"] = "error" not in data
    except Exception as e:
        print(f"❌ build_dopaminergic_network_tool failed: {e}")
        results["build_dopaminergic_network_tool"] = False
    
    # Test cross_validate_interactions_tool
    try:
        result = cross_validate_interactions_tool(
            proteins=["SNCA", "TH"],
            databases=["string"],
            confidence_threshold=0.4
        )
        data = json.loads(result)
        results["cross_validate_interactions_tool"] = "error" not in data
    except Exception as e:
        print(f"❌ cross_validate_interactions_tool failed: {e}")
        results["cross_validate_interactions_tool"] = False
    
    # Test batch_resolve_proteins_tool
    try:
        result = batch_resolve_proteins_tool(
            identifiers=["SNCA", "PRKN"],
            target_databases=["string"]
        )
        data = json.loads(result)
        results["batch_resolve_proteins_tool"] = "error" not in data
    except Exception as e:
        print(f"❌ batch_resolve_proteins_tool failed: {e}")
        results["batch_resolve_proteins_tool"] = False
    
    # Test get_research_overview_tool
    try:
        result = get_research_overview_tool()
        data = json.loads(result)
        results["get_research_overview_tool"] = "error" not in data
    except Exception as e:
        print(f"❌ get_research_overview_tool failed: {e}")
        results["get_research_overview_tool"] = False
    
    # Test execute_pd_workflow_tool
    try:
        result = execute_pd_workflow_tool(
            target_proteins=["SNCA"],
            workflow_type="biomarker_discovery"
        )
        data = json.loads(result)
        results["execute_pd_workflow_tool"] = "error" not in data
    except Exception as e:
        print(f"❌ execute_pd_workflow_tool failed: {e}")
        results["execute_pd_workflow_tool"] = False
    
    # Summary
    successful_tools = sum(1 for result in results.values() if result)
    total_tools = len(results)
    
    print(f"\n📊 Tool Test Summary: {successful_tools}/{total_tools} tools working")
    
    for tool_name, success in results.items():
        status = "✅" if success else "❌"
        print(f"  {status} {tool_name}")
    
    return results

# ================================
# EXAMPLE USAGE AND TESTING
# ================================

if __name__ == "__main__":
    print("🧬 PD Discovery Platform - CrewAI Tools")
    print("=" * 50)
    
    # Test MCP connection
    print("\n🔌 Testing MCP Connection...")
    if validate_mcp_connection():
        print("✅ MCP server is accessible")
        
        # Run tool tests
        print("\n🧪 Running Tool Tests...")
        test_results = test_all_tools()
        
        # Example usage
        print("\n📋 Example Tool Usage:")
        print("=" * 30)
        
        print("\n1. Building dopaminergic network:")
        network_result = build_dopaminergic_network_tool(
            discovery_mode="standard",
            confidence_threshold=0.7,
            include_indirect=True,
            max_white_nodes=10
        )
        print("Network building completed")
        
        print("\n2. Cross-validating interactions:")
        validation_result = cross_validate_interactions_tool(
            proteins=["SNCA", "PRKN", "TH"],
            databases=["string", "biogrid"],
            confidence_threshold=0.5
        )
        print("Cross-validation completed")
        
        print("\n3. Getting research overview:")
        overview_result = get_research_overview_tool()
        print("Research overview retrieved")
        
    else:
        print("❌ MCP server not accessible at http://localhost:8000")
        print("   Please ensure your cross_database_mcp server is running")
        print("   Example: python -m cross_database_mcp")