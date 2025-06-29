# ppx-mcp/server.py
from fastmcp import FastMCP
from pydantic import BaseModel
import asyncio
import subprocess
import json
import os
from typing import List, Dict


class PPXProject(BaseModel):
    accession: str
    title: str
    description: str
    files: List[str]
    metadata: Dict

mcp = FastMCP("PPX Integration Server")

@mcp.tool()
async def ppx_search_projects(
    keywords: List[str] = ["Parkinson", "dopamine", "synuclein"],
    database: str = "pride",
    max_results: int = 50
) -> dict:
    """Use ppx to search for proteomics projects"""
    
    try:
        # Install ppx if not available
        subprocess.run(["pip", "install", "ppx"], check=True, capture_output=True)
        
        # Create search command
        search_term = " ".join(keywords)
        cmd = [
            "python", "-c",
            f"""
import ppx
results = ppx.find_project('{search_term}', database='{database}', max_results={max_results})
import json
print(json.dumps(results, default=str))
"""
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        projects = json.loads(result.stdout)
        
        return {
            "search_term": search_term,
            "database": database,
            "projects_found": len(projects),
            "projects": projects
        }
        
    except Exception as e:
        return {"error": f"PPX search failed: {str(e)}"}

@mcp.tool()
async def ppx_download_data(
    accession: str,
    output_dir: str = "./ppx_downloads",
    file_types: List[str] = ["processed", "metadata"]
) -> dict:
    """Download proteomics data using ppx"""
    
    try:
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        cmd = [
            "python", "-c",
            f"""
import ppx
import os
import json

os.chdir('{output_dir}')
result = ppx.find_project('{accession}')
if result:
    project = result[0] if isinstance(result, list) else result
    
    # Download metadata
    metadata = ppx.get_metadata('{accession}')
    
    # Download specific file types
    files_downloaded = []
    for file_type in {file_types}:
        try:
            downloaded = ppx.download_project('{accession}', file_filter=file_type)
            files_downloaded.extend(downloaded)
        except:
            pass
    
    result_data = {{
        'accession': '{accession}',
        'metadata': metadata,
        'files_downloaded': files_downloaded,
        'download_path': os.getcwd()
    }}
    
    print(json.dumps(result_data, default=str))
else:
    print(json.dumps({{'error': 'Project not found'}}))
"""
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        download_result = json.loads(result.stdout)
        
        return download_result
        
    except Exception as e:
        return {"error": f"PPX download failed: {str(e)}"}

@mcp.tool()
async def ppx_extract_metadata(
    accession: str,
    extract_proteins: bool = True,
    extract_experimental_design: bool = True
) -> dict:
    """Extract structured metadata from proteomics project"""
    
    try:
        cmd = [
            "python", "-c",
            f"""
import ppx
import json

# Get project metadata
metadata = ppx.get_metadata('{accession}')
project_info = ppx.find_project('{accession}')

result = {{
    'accession': '{accession}',
    'basic_metadata': metadata,
    'project_info': project_info[0] if project_info else None
}}

# Extract protein information if requested
if {extract_proteins}:
    try:
        proteins = ppx.get_proteins('{accession}')
        result['proteins'] = proteins
    except:
        result['proteins'] = 'Not available'

# Extract experimental design if requested  
if {extract_experimental_design}:
    try:
        exp_design = ppx.get_experimental_design('{accession}')
        result['experimental_design'] = exp_design
    except:
        result['experimental_design'] = 'Not available'

print(json.dumps(result, default=str))
"""
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        metadata = json.loads(result.stdout)
        
        return metadata
        
    except Exception as e:
        return {"error": f"PPX metadata extraction failed: {str(e)}"}

@mcp.tool()
async def ppx_batch_analysis(
    accessions: List[str],
    analysis_type: str = "protein_summary",
    output_dir: str = "./ppx_batch_results"
) -> dict:
    """Process multiple PD datasets in batch"""
    
    try:
        os.makedirs(output_dir, exist_ok=True)
        
        batch_results = []
        for accession in accessions:
            print(f"Processing {accession}...")
            
            # Extract metadata for each project
            metadata = await ppx_extract_metadata(accession)
            
            if "error" not in metadata:
                batch_results.append({
                    "accession": accession,
                    "status": "success",
                    "metadata": metadata,
                    "protein_count": len(metadata.get("proteins", [])) if isinstance(metadata.get("proteins"), list) else 0
                })
            else:
                batch_results.append({
                    "accession": accession,
                    "status": "failed",
                    "error": metadata["error"]
                })
        
        # Create summary
        summary = {
            "total_projects": len(accessions),
            "successful": len([r for r in batch_results if r["status"] == "success"]),
            "failed": len([r for r in batch_results if r["status"] == "failed"]),
            "results": batch_results
        }
        
        # Save results
        output_file = os.path.join(output_dir, "batch_analysis_results.json")
        with open(output_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        return summary
        
    except Exception as e:
        return {"error": f"Batch analysis failed: {str(e)}"}

@mcp.tool()
async def format_for_analysis(
    accession: str,
    output_format: str = "pandas",
    include_metadata: bool = True
) -> dict:
    """Prepare proteomics data for downstream AI analysis"""
    
    try:
        # Download and extract data
        download_result = await ppx_download_data(accession)
        metadata_result = await ppx_extract_metadata(accession)
        
        if "error" in download_result or "error" in metadata_result:
            return {"error": "Failed to retrieve data for formatting"}
        
        formatted_data = {
            "accession": accession,
            "data_location": download_result.get("download_path"),
            "files_available": download_result.get("files_downloaded", []),
            "analysis_ready": True
        }
        
        if include_metadata:
            formatted_data["metadata"] = metadata_result
            
        # Create analysis-ready summary
        if metadata_result.get("proteins"):
            proteins = metadata_result["proteins"]
            if isinstance(proteins, list):
                formatted_data["protein_summary"] = {
                    "total_proteins": len(proteins),
                    "top_proteins": proteins[:20] if len(proteins) > 20 else proteins
                }
        
        return formatted_data
        
    except Exception as e:
        return {"error": f"Data formatting failed: {str(e)}"}

@mcp.tool()
async def find_pd_protein_datasets(
    target_proteins: List[str] = ["SNCA", "PARK2", "TH", "LRRK2"],
    max_datasets: int = 10
) -> dict:
    """Find PD datasets containing specific proteins of interest"""
    
    try:
        # Search for PD datasets
        pd_projects = await ppx_search_projects(
            keywords=["Parkinson", "dopamine"],
            max_results=max_datasets * 2  # Get more to filter
        )
        
        if "error" in pd_projects:
            return pd_projects
        
        matching_datasets = []
        for project in pd_projects["projects"][:max_datasets]:
            accession = project.get("accession") or project.get("id")
            if not accession:
                continue
                
            # Extract metadata to check for target proteins
            metadata = await ppx_extract_metadata(accession, extract_proteins=True)
            
            if "error" not in metadata and metadata.get("proteins"):
                proteins = metadata["proteins"]
                if isinstance(proteins, list):
                    # Check if any target proteins are present
                    protein_names = [str(p).upper() for p in proteins]
                    found_proteins = [tp for tp in target_proteins if tp.upper() in protein_names]
                    
                    if found_proteins:
                        matching_datasets.append({
                            "accession": accession,
                            "project_info": project,
                            "found_proteins": found_proteins,
                            "total_proteins": len(proteins)
                        })
        
        return {
            "target_proteins": target_proteins,
            "datasets_found": len(matching_datasets),
            "matching_datasets": matching_datasets
        }
        
    except Exception as e:
        return {"error": f"PD protein dataset search failed: {str(e)}"}

if __name__ == "__main__":
    # Check if running in Docker (HTTP mode) or locally (stdio mode)
    if os.getenv("DOCKER_MODE") == "true":
        # Run with HTTP transport for Docker
        mcp.run(transport="http", host="0.0.0.0", port=8000)
    else:
        # Run with stdio transport for local development
        mcp.run()