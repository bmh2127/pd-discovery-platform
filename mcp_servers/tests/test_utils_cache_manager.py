# tests/test_utils_cache_manager.py
import pytest
from datetime import datetime, timedelta
from mcp_servers.cross_database_mcp.utils.cache_manager import ProteinCacheManager

class TestProteinCacheManager:
    """Test suite for ProteinCacheManager"""

    def setup_method(self):
        """Setup fresh cache manager for each test"""
        self.cache_manager = ProteinCacheManager()

    def test_cache_initialization(self):
        """Test cache manager initializes correctly"""
        assert hasattr(self.cache_manager, '_cache')
        assert hasattr(self.cache_manager, '_default_ttl')
        assert isinstance(self.cache_manager._cache, dict)
        assert len(self.cache_manager._cache) == 0

    def test_set_and_get_protein_data(self):
        """Test basic set and get operations"""
        protein_data = {
            "query": "SNCA",
            "status": "resolved",
            "database_mappings": {"string": {"id": "9606.ENSP00000002434"}}
        }
        
        # Set data
        self.cache_manager.set("SNCA", protein_data)
        
        # Get data
        retrieved_data = self.cache_manager.get("SNCA")
        assert retrieved_data is not None
        assert retrieved_data["query"] == "SNCA"
        assert retrieved_data["status"] == "resolved"
        assert "cache_metadata" in retrieved_data
        assert "resolved_at" in retrieved_data["cache_metadata"]

    def test_case_insensitive_storage(self):
        """Test that protein identifiers are stored case-insensitively"""
        protein_data = {"query": "snca", "status": "resolved"}
        
        # Set with lowercase
        self.cache_manager.set("snca", protein_data)
        
        # Get with uppercase
        retrieved_data = self.cache_manager.get("SNCA")
        assert retrieved_data is not None
        assert retrieved_data["query"] == "snca"
        
        # Get with mixed case
        retrieved_data = self.cache_manager.get("Snca")
        assert retrieved_data is not None

    def test_cache_expiration(self):
        """Test that expired cache entries are cleaned up"""
        # Create cache manager with very short TTL for testing
        test_cache = ProteinCacheManager()
        test_cache._default_ttl = timedelta(milliseconds=1)  # 1ms TTL
        
        protein_data = {"query": "SNCA", "status": "resolved"}
        test_cache.set("SNCA", protein_data)
        
        # Should be retrievable immediately
        assert test_cache.get("SNCA") is not None
        
        # Wait for expiration
        import time
        time.sleep(0.01)  # 10ms
        
        # Should be expired and cleaned up
        assert test_cache.get("SNCA") is None

    def test_cache_metadata_injection(self):
        """Test that cache metadata is properly injected"""
        protein_data = {"query": "SNCA", "status": "resolved"}
        
        self.cache_manager.set("SNCA", protein_data)
        retrieved_data = self.cache_manager.get("SNCA")
        
        assert "cache_metadata" in retrieved_data
        metadata = retrieved_data["cache_metadata"]
        assert "resolved_at" in metadata
        
        # Should be a valid ISO timestamp
        resolved_at = datetime.fromisoformat(metadata["resolved_at"])
        assert isinstance(resolved_at, datetime)
        
        # Should be recent
        now = datetime.now()
        assert (now - resolved_at).total_seconds() < 1

    def test_cache_invalidation(self):
        """Test manual cache invalidation"""
        protein_data = {"query": "SNCA", "status": "resolved"}
        
        # Set and verify
        self.cache_manager.set("SNCA", protein_data)
        assert self.cache_manager.get("SNCA") is not None
        
        # Invalidate and verify
        self.cache_manager.invalidate("SNCA")
        assert self.cache_manager.get("SNCA") is None

    def test_multiple_proteins_storage(self):
        """Test storing multiple different proteins"""
        proteins = {
            "SNCA": {"query": "SNCA", "status": "resolved", "confidence": 0.95},
            "PARK2": {"query": "PARK2", "status": "resolved", "confidence": 0.92},
            "TH": {"query": "TH", "status": "resolved", "confidence": 0.88}
        }
        
        # Store all proteins
        for identifier, data in proteins.items():
            self.cache_manager.set(identifier, data)
        
        # Verify all can be retrieved
        for identifier, expected_data in proteins.items():
            retrieved_data = self.cache_manager.get(identifier)
            assert retrieved_data is not None
            assert retrieved_data["query"] == expected_data["query"]
            assert retrieved_data["confidence"] == expected_data["confidence"]

    def test_cache_overwrite(self):
        """Test that setting data for the same protein overwrites previous data"""
        # Set initial data
        initial_data = {"query": "SNCA", "status": "processing", "confidence": 0.0}
        self.cache_manager.set("SNCA", initial_data)
        
        # Set updated data
        updated_data = {"query": "SNCA", "status": "resolved", "confidence": 0.95}
        self.cache_manager.set("SNCA", updated_data)
        
        # Should get updated data
        retrieved_data = self.cache_manager.get("SNCA")
        assert retrieved_data["status"] == "resolved"
        assert retrieved_data["confidence"] == 0.95

    def test_nonexistent_protein_get(self):
        """Test getting data for protein that doesn't exist in cache"""
        result = self.cache_manager.get("NONEXISTENT_PROTEIN")
        assert result is None

    def test_cache_preserves_complex_data_structures(self):
        """Test that complex nested data structures are preserved"""
        complex_data = {
            "query": "SNCA",
            "status": "resolved",
            "database_mappings": {
                "string": {
                    "id": "9606.ENSP00000002434",
                    "name": "SNCA",
                    "annotations": ["Parkinson's disease", "alpha-synuclein"]
                },
                "pride": {
                    "dataset_count": 15,
                    "sample_projects": ["PXD015293", "PXD037684"]
                }
            },
            "confidence_scores": {
                "string": 0.95,
                "pride": 0.85
            },
            "metadata": {
                "resolved_at": "2024-01-01T12:00:00",
                "research_priority": "high",
                "aliases": ["alpha-synuclein", "NACP"]
            }
        }
        
        self.cache_manager.set("SNCA", complex_data)
        retrieved_data = self.cache_manager.get("SNCA")
        
        # Verify complex structure is preserved
        assert retrieved_data["database_mappings"]["string"]["id"] == "9606.ENSP00000002434"
        assert len(retrieved_data["database_mappings"]["string"]["annotations"]) == 2
        assert retrieved_data["confidence_scores"]["string"] == 0.95
        assert "alpha-synuclein" in retrieved_data["metadata"]["aliases"]

    def test_concurrent_cache_operations(self):
        """Test that cache handles concurrent operations correctly"""
        import threading
        import time
        
        results = []
        
        def cache_operation(protein_id, data):
            self.cache_manager.set(protein_id, data)
            time.sleep(0.001)  # Small delay
            retrieved = self.cache_manager.get(protein_id)
            results.append((protein_id, retrieved is not None))
        
        # Start multiple threads
        threads = []
        for i in range(10):
            protein_data = {"query": f"PROTEIN_{i}", "status": "resolved"}
            thread = threading.Thread(
                target=cache_operation, 
                args=(f"PROTEIN_{i}", protein_data)
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Verify all operations succeeded
        assert len(results) == 10
        assert all(success for _, success in results) 