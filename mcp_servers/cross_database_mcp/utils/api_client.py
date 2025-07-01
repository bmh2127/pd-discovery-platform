import httpx
import asyncio
from typing import Dict, Any, Optional
from ..config import STRING_MCP_URL, PRIDE_MCP_URL, BIOGRID_MCP_URL

class CrossDatabaseAPIClient:
    def __init__(self):
        self.endpoints = {
            "string": STRING_MCP_URL,
            "pride": PRIDE_MCP_URL,
            "biogrid": BIOGRID_MCP_URL
        }
    
    async def call_mcp_tool(self, service: str, tool_name: str, arguments: Dict[str, Any], timeout: float = 30.0) -> Optional[Dict]:
        """Centralized MCP tool calling with error handling"""
        if service not in self.endpoints:
            raise ValueError(f"Unknown service: {service}")
            
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    f"{self.endpoints[service]}/call_tool",
                    json={"name": tool_name, "arguments": arguments}
                )
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"API call failed: {service}.{tool_name} - {response.status_code}")
                    return None
        except Exception as e:
            print(f"API call error: {service}.{tool_name} - {e}")
            return None
    
    async def read_mcp_resource(self, service: str, resource_uri: str, timeout: float = 30.0) -> Optional[Dict]:
        """Centralized MCP resource reading"""
        if service not in self.endpoints:
            raise ValueError(f"Unknown service: {service}")
            
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(
                    f"{self.endpoints[service]}/read_resource",
                    params={"uri": resource_uri}
                )
                if response.status_code == 200:
                    return response.json()
                else:
                    return None
        except Exception as e:
            print(f"Resource read error: {service} - {resource_uri} - {e}")
            return None

# Global instance
api_client = CrossDatabaseAPIClient()