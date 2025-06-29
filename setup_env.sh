#!/bin/bash

# setup_env.sh - Environment setup for MCP Cross-Database Integration

echo "Setting up environment for MCP Cross-Database Integration..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << 'EOF'
# MCP Service URLs for Cross-Database Integration
# Local development URLs (when running MCP servers individually)
STRING_MCP_URL=http://localhost:8001
PRIDE_MCP_URL=http://localhost:8002
BIOGRID_MCP_URL=http://localhost:8003
PPX_MCP_URL=http://localhost:8004

# Docker service URLs (when running in containers)
# Uncomment these and comment above when using Docker Compose
# STRING_MCP_URL=http://string_mcp:8000
# PRIDE_MCP_URL=http://pride_mcp:8000
# BIOGRID_MCP_URL=http://biogrid_mcp:8000
# PPX_MCP_URL=http://ppx_mcp:8000

# API Keys
BIOGRID_API_KEY=your_biogrid_api_key_here
STRING_IDENTITY=your_string_identity_here

# Docker Mode Flag
DOCKER_MODE=false
EOF
    echo ".env file created successfully!"
else
    echo ".env file already exists."
fi

# Function to switch to local development mode
setup_local() {
    echo "Configuring for LOCAL DEVELOPMENT mode..."
    sed -i.bak 's/^# STRING_MCP_URL=http:\/\/localhost/STRING_MCP_URL=http:\/\/localhost/' .env
    sed -i.bak 's/^# PRIDE_MCP_URL=http:\/\/localhost/PRIDE_MCP_URL=http:\/\/localhost/' .env
    sed -i.bak 's/^# BIOGRID_MCP_URL=http:\/\/localhost/BIOGRID_MCP_URL=http:\/\/localhost/' .env
    sed -i.bak 's/^# PPX_MCP_URL=http:\/\/localhost/PPX_MCP_URL=http:\/\/localhost/' .env
    sed -i.bak 's/^STRING_MCP_URL=http:\/\/string_mcp/# STRING_MCP_URL=http:\/\/string_mcp/' .env
    sed -i.bak 's/^PRIDE_MCP_URL=http:\/\/pride_mcp/# PRIDE_MCP_URL=http:\/\/pride_mcp/' .env
    sed -i.bak 's/^BIOGRID_MCP_URL=http:\/\/biogrid_mcp/# BIOGRID_MCP_URL=http:\/\/biogrid_mcp/' .env
    sed -i.bak 's/^PPX_MCP_URL=http:\/\/ppx_mcp/# PPX_MCP_URL=http:\/\/ppx_mcp/' .env
    sed -i.bak 's/^DOCKER_MODE=true/DOCKER_MODE=false/' .env
    echo "Local development mode configured!"
    echo "Make sure to run each MCP server on its configured port:"
    echo "  - STRING MCP: port 8001"
    echo "  - PRIDE MCP: port 8002"
    echo "  - BIOGRID MCP: port 8003"
    echo "  - PPX MCP: port 8004"
    echo "  - Cross Database MCP: port 8005"
}

# Function to switch to Docker mode
setup_docker() {
    echo "Configuring for DOCKER COMPOSE mode..."
    sed -i.bak 's/^STRING_MCP_URL=http:\/\/localhost/# STRING_MCP_URL=http:\/\/localhost/' .env
    sed -i.bak 's/^PRIDE_MCP_URL=http:\/\/localhost/# PRIDE_MCP_URL=http:\/\/localhost/' .env
    sed -i.bak 's/^BIOGRID_MCP_URL=http:\/\/localhost/# BIOGRID_MCP_URL=http:\/\/localhost/' .env
    sed -i.bak 's/^PPX_MCP_URL=http:\/\/localhost/# PPX_MCP_URL=http:\/\/localhost/' .env
    sed -i.bak 's/^# STRING_MCP_URL=http:\/\/string_mcp/STRING_MCP_URL=http:\/\/string_mcp/' .env
    sed -i.bak 's/^# PRIDE_MCP_URL=http:\/\/pride_mcp/PRIDE_MCP_URL=http:\/\/pride_mcp/' .env
    sed -i.bak 's/^# BIOGRID_MCP_URL=http:\/\/biogrid_mcp/BIOGRID_MCP_URL=http:\/\/biogrid_mcp/' .env
    sed -i.bak 's/^# PPX_MCP_URL=http:\/\/ppx_mcp/PPX_MCP_URL=http:\/\/ppx_mcp/' .env
    sed -i.bak 's/^DOCKER_MODE=false/DOCKER_MODE=true/' .env
    echo "Docker Compose mode configured!"
    echo "Use 'docker-compose up' to start all services"
}

# Check command line argument
case "$1" in
    "local")
        setup_local
        ;;
    "docker")
        setup_docker
        ;;
    *)
        echo "Usage: $0 [local|docker]"
        echo ""
        echo "Commands:"
        echo "  local  - Configure for local development (individual MCP servers)"
        echo "  docker - Configure for Docker Compose deployment"
        echo ""
        echo "Without arguments, just creates the .env template"
        ;;
esac

echo "Environment setup complete!" 