from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from ..config import PROTEIN_CACHE_TTL_HOURS

class ProteinCacheManager:
    def __init__(self):
        self._cache: Dict[str, Dict] = {}
        self._default_ttl = timedelta(hours=PROTEIN_CACHE_TTL_HOURS)
    
    def get(self, identifier: str) -> Optional[Dict]:
        """Get cached protein data if not expired"""
        cache_key = identifier.upper()
        if cache_key not in self._cache:
            return None
            
        cached_data = self._cache[cache_key]
        cache_time = datetime.fromisoformat(cached_data["cache_metadata"]["resolved_at"])
        
        if datetime.now() - cache_time < self._default_ttl:
            return cached_data
        else:
            # Clean up expired cache
            del self._cache[cache_key]
            return None
    
    def set(self, identifier: str, data: Dict) -> None:
        """Cache protein data with timestamp"""
        cache_key = identifier.upper()
        data["cache_metadata"] = {
            **data.get("cache_metadata", {}),
            "resolved_at": datetime.now().isoformat()
        }
        self._cache[cache_key] = data
    
    def invalidate(self, identifier: str) -> None:
        """Invalidate specific protein cache"""
        cache_key = identifier.upper()
        if cache_key in self._cache:
            del self._cache[cache_key]

# Global instance
protein_cache = ProteinCacheManager()