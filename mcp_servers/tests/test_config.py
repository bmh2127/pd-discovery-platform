# tests/test_config.py
import pytest
import os
from unittest.mock import patch
from mcp_servers.cross_database_mcp import config

class TestConfig:
    """Test suite for configuration module"""

    def test_default_config_values(self):
        """Test that default configuration values are set correctly"""
        # Test default URLs
        assert "localhost:8001" in config.STRING_MCP_URL
        assert "localhost:8002" in config.PRIDE_MCP_URL  
        assert "localhost:8003" in config.BIOGRID_MCP_URL

        # Test default cache and timeout values
        assert config.PROTEIN_CACHE_TTL_HOURS == 24
        assert config.DEFAULT_TIMEOUT_SECONDS == 30

    def test_environment_variable_override(self):
        """Test that environment variables override defaults"""
        test_env_vars = {
            'STRING_MCP_URL': 'http://custom-string:9001',
            'PRIDE_MCP_URL': 'http://custom-pride:9002',
            'BIOGRID_MCP_URL': 'http://custom-biogrid:9003'
        }

        with patch.dict(os.environ, test_env_vars):
            # Reload the config module to pick up environment changes
            import importlib
            importlib.reload(config)

            # Verify environment variables are used
            assert config.STRING_MCP_URL == 'http://custom-string:9001'
            assert config.PRIDE_MCP_URL == 'http://custom-pride:9002'
            assert config.BIOGRID_MCP_URL == 'http://custom-biogrid:9003'

    def test_docker_environment_urls(self):
        """Test Docker service name URLs"""
        docker_env_vars = {
            'STRING_MCP_URL': 'http://string_mcp:8000',
            'PRIDE_MCP_URL': 'http://pride_mcp:8000',
            'BIOGRID_MCP_URL': 'http://biogrid_mcp:8000'
        }

        with patch.dict(os.environ, docker_env_vars):
            import importlib
            importlib.reload(config)

            # Verify Docker service URLs are used
            assert config.STRING_MCP_URL == 'http://string_mcp:8000'
            assert config.PRIDE_MCP_URL == 'http://pride_mcp:8000'
            assert config.BIOGRID_MCP_URL == 'http://biogrid_mcp:8000'

    def test_production_environment_urls(self):
        """Test production environment URLs"""
        prod_env_vars = {
            'STRING_MCP_URL': 'https://string-api.production.com',
            'PRIDE_MCP_URL': 'https://pride-api.production.com',
            'BIOGRID_MCP_URL': 'https://biogrid-api.production.com'
        }

        with patch.dict(os.environ, prod_env_vars):
            import importlib
            importlib.reload(config)

            # Verify production URLs are used
            assert config.STRING_MCP_URL == 'https://string-api.production.com'
            assert config.PRIDE_MCP_URL == 'https://pride-api.production.com'
            assert config.BIOGRID_MCP_URL == 'https://biogrid-api.production.com'

    def test_config_constants_are_importable(self):
        """Test that all expected configuration constants exist and are importable"""
        # Test URL constants exist
        assert hasattr(config, 'STRING_MCP_URL')
        assert hasattr(config, 'PRIDE_MCP_URL')
        assert hasattr(config, 'BIOGRID_MCP_URL')

        # Test cache/timeout constants exist
        assert hasattr(config, 'PROTEIN_CACHE_TTL_HOURS')
        assert hasattr(config, 'DEFAULT_TIMEOUT_SECONDS')

        # Test all are strings or numbers as expected
        assert isinstance(config.STRING_MCP_URL, str)
        assert isinstance(config.PRIDE_MCP_URL, str)
        assert isinstance(config.BIOGRID_MCP_URL, str)
        assert isinstance(config.PROTEIN_CACHE_TTL_HOURS, int)
        assert isinstance(config.DEFAULT_TIMEOUT_SECONDS, int)

    def test_url_format_validation(self):
        """Test that URLs have valid format"""
        # URLs should start with http:// or https://
        assert config.STRING_MCP_URL.startswith(('http://', 'https://'))
        assert config.PRIDE_MCP_URL.startswith(('http://', 'https://'))
        assert config.BIOGRID_MCP_URL.startswith(('http://', 'https://'))

        # URLs should not end with slash
        assert not config.STRING_MCP_URL.endswith('/')
        assert not config.PRIDE_MCP_URL.endswith('/')
        assert not config.BIOGRID_MCP_URL.endswith('/')

    def test_cache_ttl_reasonable_value(self):
        """Test that cache TTL is a reasonable value"""
        # Should be positive
        assert config.PROTEIN_CACHE_TTL_HOURS > 0
        
        # Should be reasonable (between 1 hour and 1 week)
        assert 1 <= config.PROTEIN_CACHE_TTL_HOURS <= 168

    def test_timeout_reasonable_value(self):
        """Test that timeout is a reasonable value"""
        # Should be positive
        assert config.DEFAULT_TIMEOUT_SECONDS > 0
        
        # Should be reasonable (between 5 seconds and 5 minutes)
        assert 5 <= config.DEFAULT_TIMEOUT_SECONDS <= 300

    def test_config_reload_safety(self):
        """Test that config can be safely reloaded multiple times"""
        import importlib
        
        # Store original values
        original_string_url = config.STRING_MCP_URL
        original_pride_url = config.PRIDE_MCP_URL
        original_biogrid_url = config.BIOGRID_MCP_URL

        # Reload multiple times
        for _ in range(3):
            importlib.reload(config)

        # Values should remain consistent
        assert config.STRING_MCP_URL == original_string_url
        assert config.PRIDE_MCP_URL == original_pride_url
        assert config.BIOGRID_MCP_URL == original_biogrid_url

    def test_partial_environment_override(self):
        """Test that partial environment variable override works"""
        # Only override one URL
        test_env_vars = {
            'STRING_MCP_URL': 'http://custom-string-only:9001'
        }

        with patch.dict(os.environ, test_env_vars, clear=False):
            import importlib
            importlib.reload(config)

            # STRING URL should be overridden
            assert config.STRING_MCP_URL == 'http://custom-string-only:9001'
            
            # Others should still be defaults
            assert "localhost:8002" in config.PRIDE_MCP_URL
            assert "localhost:8003" in config.BIOGRID_MCP_URL

    def test_empty_environment_variable_handling(self):
        """Test handling of empty environment variables"""
        test_env_vars = {
            'STRING_MCP_URL': '',
            'PRIDE_MCP_URL': '',
            'BIOGRID_MCP_URL': ''
        }

        with patch.dict(os.environ, test_env_vars):
            import importlib
            importlib.reload(config)

            # Empty strings should fall back to defaults
            assert "localhost:8001" in config.STRING_MCP_URL
            assert "localhost:8002" in config.PRIDE_MCP_URL
            assert "localhost:8003" in config.BIOGRID_MCP_URL

    def teardown_method(self):
        """Clean up after each test by reloading config with original environment"""
        import importlib
        
        # Clear any test environment variables that might affect subsequent tests
        test_vars = ['STRING_MCP_URL', 'PRIDE_MCP_URL', 'BIOGRID_MCP_URL']
        for var in test_vars:
            if var in os.environ:
                del os.environ[var]
        
        # Reload config to restore defaults
        importlib.reload(config) 