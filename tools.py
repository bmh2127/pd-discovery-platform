from crewai.tools import tool
from crewai_tools import SerperDevTool
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

# ================================
# WORKING SERPER API IMPLEMENTATION  
# ================================

def serper_search_function(search_query: str) -> str:
    """Core search function using Serper API that returns real URLs and content.
    
    Args:
        search_query (str): The search query to execute
        
    Returns:
        str: Search results with real URLs and descriptions
    """
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        return "Error: SERPER_API_KEY not found in environment variables"
    
    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }
    
    payload = {
        "q": search_query,
        "num": 10  # Get 10 results
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # Format results
            results = []
            
            # Add organic results
            if "organic" in data:
                for i, result in enumerate(data["organic"][:8], 1):
                    title = result.get("title", "No title")
                    link = result.get("link", "")
                    snippet = result.get("snippet", "No description")
                    
                    results.append(f"{i}. **{title}**")
                    results.append(f"   URL: {link}")
                    results.append(f"   Description: {snippet}")
                    results.append("")
            
            # Add related searches if available
            if "relatedSearches" in data:
                results.append("**Related Searches:**")
                for related in data["relatedSearches"][:3]:
                    results.append(f"- {related.get('query', '')}")
                results.append("")
            
            return "\n".join(results) if results else "No results found"
            
        else:
            return f"Search API error: {response.status_code} - {response.text}"
            
    except Exception as e:
        return f"Search failed: {str(e)}"

@tool("Search the internet with Serper")
def working_serper_search(search_query: str) -> str:
    """Search the internet using Serper API and return real URLs and content.
    
    Args:
        search_query (str): The search query to execute
        
    Returns:
        str: Search results with real URLs and descriptions
    """
    return serper_search_function(search_query)

# Create working search tools for different purposes
academic_search_tool = working_serper_search
code_search_tool = working_serper_search 
educational_search_tool = working_serper_search
research_tool = working_serper_search

# For backwards compatibility, create aliases with the original names
firecrawl_academic_search_tool = academic_search_tool
firecrawl_code_search_tool = code_search_tool
firecrawl_educational_search_tool = educational_search_tool
firecrawl_research_tool = research_tool

# ================================
# BRIGHTDATA API EXTRACTION TOOL
# ================================

@tool("Website Content Extraction with BrightData")
def firecrawl_extract_tool(input_data: str) -> str:
    """Extracts specific content from websites using BrightData MCP for robust extraction.
    Handles GitHub and other websites with anti-bot protection much better than Firecrawl.
    
    Input should be in the format: "URL|extraction instructions"
    Example: "https://github.com/trending|Extract the top 5 trending repositories with descriptions"
    """
    try:
        parts = input_data.split("|", 1)
        if len(parts) != 2:
            return "Invalid input format. Please use: URL|extraction instructions"
        
        url, instructions = parts
        url = url.strip()
        instructions = instructions.strip()
        
        print(f"Extracting content from: {url}")
        
        try:
            # Use BrightData MCP tools for robust extraction
            # Try different extraction methods based on URL type
            
            if "github.com" in url.lower():
                print("Using BrightData GitHub extraction...")
                # For GitHub URLs, try the GitHub repository file extraction
                try:
                    # This uses the MCP tool available in your environment
                    from mcp_Bright_Data_web_data_github_repository_file import mcp_Bright_Data_web_data_github_repository_file
                    result = mcp_Bright_Data_web_data_github_repository_file(url)
                    if result and len(str(result)) > 100:
                        return f"GitHub content extracted from {url}:\n\n{str(result)[:2000]}..."
                except Exception as github_err:
                    print(f"GitHub-specific extraction failed: {github_err}")
            
            # For all URLs (including GitHub fallback), use general markdown extraction
            print("Using BrightData markdown extraction...")
            try:
                # This uses the MCP tool available in your environment  
                from mcp_Bright_Data_scrape_as_markdown import mcp_Bright_Data_scrape_as_markdown
                result = mcp_Bright_Data_scrape_as_markdown(url)
                
                if result and len(str(result)) > 100:
                    content = str(result)[:2000]
                    return f"Successfully extracted content from {url} (Instructions: {instructions}):\n\n{content}..."
                else:
                    print("BrightData returned minimal content, trying fallback...")
            except Exception as mcp_err:
                print(f"BrightData MCP extraction failed: {mcp_err}")
            
            # Fallback: Use requests with proper headers for basic extraction
            print("Using fallback HTTP extraction...")
            fallback_headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            }
            
            response = requests.get(url, headers=fallback_headers, timeout=30)
            
            if response.status_code == 200:
                content = response.text
                
                if content and len(content) > 100:
                    # Extract text content (simplified)
                    import re
                    # Remove HTML tags for better readability
                    text_content = re.sub(r'<[^>]+>', '', content)
                    # Clean up whitespace
                    text_content = re.sub(r'\s+', ' ', text_content).strip()
                    
                    return f"Fallback extraction successful from {url} (Instructions: {instructions}):\n\n{text_content[:2000]}..."
                else:
                    return f"Extraction returned minimal content for {url}. The page may be restricted or empty."
            else:
                return f"HTTP request failed with status {response.status_code} for {url}"
                
        except Exception as extract_err:
            return f"All extraction methods failed for {url}: {extract_err}"
            
    except Exception as e:
        return f"Error in content extraction: {str(e)}"