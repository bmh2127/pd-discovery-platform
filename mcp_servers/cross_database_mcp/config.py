import os

# MCP endpoint configuration
STRING_MCP_URL = os.getenv("STRING_MCP_URL", "http://localhost:8001")
PRIDE_MCP_URL = os.getenv("PRIDE_MCP_URL", "http://localhost:8002")
BIOGRID_MCP_URL = os.getenv("BIOGRID_MCP_URL", "http://localhost:8003")

# Cache configuration
PROTEIN_CACHE_TTL_HOURS = 24
DEFAULT_TIMEOUT_SECONDS = 30