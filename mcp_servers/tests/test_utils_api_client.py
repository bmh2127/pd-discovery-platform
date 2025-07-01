# tests/test_utils_api_client.py
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, Mock
import httpx
from mcp_servers.cross_database_mcp.utils.api_client import CrossDatabaseAPIClient

class TestCrossDatabaseAPIClient:
    """Test suite for CrossDatabaseAPIClient"""

    def setup_method(self):
        """Setup fresh API client for each test"""
        self.api_client = CrossDatabaseAPIClient()

    def test_client_initialization(self):
        """Test API client initializes with correct endpoints"""
        assert hasattr(self.api_client, 'endpoints')
        assert isinstance(self.api_client.endpoints, dict)
        
        # Should have all required services
        expected_services = ["string", "pride", "biogrid"]
        for service in expected_services:
            assert service in self.api_client.endpoints

        # Should have default URLs
        assert "localhost:8001" in self.api_client.endpoints["string"]
        assert "localhost:8002" in self.api_client.endpoints["pride"]
        assert "localhost:8003" in self.api_client.endpoints["biogrid"]

    @pytest.mark.asyncio
    async def test_successful_mcp_tool_call(self):
        """Test successful MCP tool call"""
        mock_response_data = {
            "mapped_proteins": [
                {
                    "stringId": "9606.ENSP00000002434",
                    "preferredName": "SNCA",
                    "annotation": "Synuclein alpha"
                }
            ]
        }

        with patch('httpx.AsyncClient') as mock_client_class:
            # Setup mock
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_client.post = AsyncMock(return_value=mock_response)

            # Test call
            result = await self.api_client.call_mcp_tool(
                "string", "map_proteins", {"proteins": ["SNCA"], "species": 9606}
            )

            # Verify result
            assert result is not None
            assert "mapped_proteins" in result
            assert result["mapped_proteins"][0]["preferredName"] == "SNCA"

            # Verify HTTP call was made correctly
            mock_client.post.assert_called_once_with(
                "http://localhost:8001/call_tool",
                json={"name": "map_proteins", "arguments": {"proteins": ["SNCA"], "species": 9606}}
            )

    @pytest.mark.asyncio
    async def test_failed_mcp_tool_call_http_error(self):
        """Test MCP tool call with HTTP error"""
        with patch('httpx.AsyncClient') as mock_client_class:
            # Setup mock for HTTP error
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
            
            mock_response = Mock()
            mock_response.status_code = 500
            mock_client.post = AsyncMock(return_value=mock_response)

            # Test call
            result = await self.api_client.call_mcp_tool(
                "string", "map_proteins", {"proteins": ["SNCA"]}
            )

            # Should return None for failed call
            assert result is None

    @pytest.mark.asyncio
    async def test_mcp_tool_call_connection_error(self):
        """Test MCP tool call with connection error"""
        with patch('httpx.AsyncClient') as mock_client_class:
            # Setup mock for connection error
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
            
            mock_client.post = AsyncMock(side_effect=httpx.ConnectError("Connection failed"))

            # Test call
            result = await self.api_client.call_mcp_tool(
                "string", "map_proteins", {"proteins": ["SNCA"]}
            )

            # Should return None for connection error
            assert result is None

    @pytest.mark.asyncio
    async def test_mcp_tool_call_timeout(self):
        """Test MCP tool call with timeout"""
        with patch('httpx.AsyncClient') as mock_client_class:
            # Setup mock for timeout
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
            
            mock_client.post = AsyncMock(side_effect=asyncio.TimeoutError())

            # Test call
            result = await self.api_client.call_mcp_tool(
                "string", "map_proteins", {"proteins": ["SNCA"]}, timeout=1.0
            )

            # Should return None for timeout
            assert result is None

    @pytest.mark.asyncio
    async def test_unknown_service_error(self):
        """Test calling tool on unknown service"""
        with pytest.raises(ValueError) as excinfo:
            await self.api_client.call_mcp_tool(
                "unknown_service", "some_tool", {"param": "value"}
            )
        
        assert "Unknown service: unknown_service" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_successful_resource_read(self):
        """Test successful MCP resource read"""
        mock_resource_data = {
            "biomarkers": {
                "established": ["SNCA", "PRKN", "TH"],
                "emerging": ["LRRK2", "PINK1"]
            }
        }

        with patch('httpx.AsyncClient') as mock_client_class:
            # Setup mock
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_resource_data
            mock_client.get = AsyncMock(return_value=mock_response)

            # Test call
            result = await self.api_client.read_mcp_resource(
                "string", "dopaminergic://markers"
            )

            # Verify result
            assert result is not None
            assert "biomarkers" in result
            assert "SNCA" in result["biomarkers"]["established"]

            # Verify HTTP call was made correctly
            mock_client.get.assert_called_once_with(
                "http://localhost:8001/read_resource",
                params={"uri": "dopaminergic://markers"}
            )

    @pytest.mark.asyncio
    async def test_failed_resource_read(self):
        """Test failed MCP resource read"""
        with patch('httpx.AsyncClient') as mock_client_class:
            # Setup mock for failure
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
            
            mock_response = Mock()
            mock_response.status_code = 404
            mock_client.get = AsyncMock(return_value=mock_response)

            # Test call
            result = await self.api_client.read_mcp_resource(
                "string", "nonexistent://resource"
            )

            # Should return None for failed read
            assert result is None

    @pytest.mark.asyncio
    async def test_multiple_concurrent_calls(self):
        """Test multiple concurrent API calls"""
        mock_responses = [
            {"service": "string", "data": "string_data"},
            {"service": "pride", "data": "pride_data"},
            {"service": "biogrid", "data": "biogrid_data"}
        ]

        with patch('httpx.AsyncClient') as mock_client_class:
            # Setup mock for multiple responses
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
            
            # Create mock responses
            mock_responses_objs = []
            for mock_data in mock_responses:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = mock_data
                mock_responses_objs.append(mock_response)
            
            mock_client.post = AsyncMock(side_effect=mock_responses_objs)

            # Test concurrent calls
            tasks = []
            for i, service in enumerate(["string", "pride", "biogrid"]):
                task = self.api_client.call_mcp_tool(
                    service, "test_tool", {"param": f"value_{i}"}
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)

            # Verify all calls succeeded
            assert len(results) == 3
            for i, result in enumerate(results):
                assert result is not None
                assert result["service"] == ["string", "pride", "biogrid"][i]

    @pytest.mark.asyncio
    async def test_custom_timeout_parameter(self):
        """Test that custom timeout parameter is used"""
        with patch('httpx.AsyncClient') as mock_client_class:
            # Setup mock
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"test": "data"}
            mock_client.post = AsyncMock(return_value=mock_response)

            # Test call with custom timeout
            await self.api_client.call_mcp_tool(
                "string", "test_tool", {"param": "value"}, timeout=60.0
            )

            # Verify AsyncClient was created with custom timeout
            mock_client_class.assert_called_with(timeout=60.0)

    @pytest.mark.asyncio
    async def test_all_supported_services(self):
        """Test calls to all supported services"""
        services = ["string", "pride", "biogrid"]
        
        with patch('httpx.AsyncClient') as mock_client_class:
            # Setup mock
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"success": True}
            mock_client.post = AsyncMock(return_value=mock_response)

            # Test each service
            for service in services:
                result = await self.api_client.call_mcp_tool(
                    service, "test_tool", {"param": "value"}
                )
                assert result is not None
                assert result["success"] is True

    @pytest.mark.asyncio
    async def test_proper_request_format(self):
        """Test that requests are formatted correctly"""
        tool_name = "map_proteins"
        arguments = {"proteins": ["SNCA", "TH"], "species": 9606}

        with patch('httpx.AsyncClient') as mock_client_class:
            # Setup mock
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"test": "response"}
            mock_client.post = AsyncMock(return_value=mock_response)

            # Test call
            await self.api_client.call_mcp_tool("string", tool_name, arguments)

            # Verify request format
            expected_json = {"name": tool_name, "arguments": arguments}
            mock_client.post.assert_called_once_with(
                "http://localhost:8001/call_tool",
                json=expected_json
            )

    @pytest.mark.asyncio
    async def test_error_logging(self):
        """Test that errors are properly logged (printed)"""
        with patch('httpx.AsyncClient') as mock_client_class, \
             patch('builtins.print') as mock_print:
            
            # Setup mock for connection error
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
            
            mock_client.post = AsyncMock(side_effect=Exception("Test error"))

            # Test call
            result = await self.api_client.call_mcp_tool(
                "string", "test_tool", {"param": "value"}
            )

            # Should return None and print error
            assert result is None
            mock_print.assert_called()
            
            # Check that error message was printed
            printed_args = mock_print.call_args[0]
            assert "API call error" in printed_args[0]
            assert "string.test_tool" in printed_args[0] 