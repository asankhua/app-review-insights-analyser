"""
Cache service for reducing API calls across phases
"""
import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from pathlib import Path
from src.config.settings import Config

logger = logging.getLogger(__name__)

class CacheService:
    """Simple file-based cache for API responses"""
    
    def __init__(self):
        self.config = Config()
        self.cache_dir = Path("data/cache")
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_ttl = timedelta(hours=1)  # Cache for 1 hour
    
    def _get_cache_key(self, data: Dict[str, Any]) -> str:
        """Generate cache key from data"""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.md5(data_str.encode()).hexdigest()
    
    def _get_cache_path(self, key: str, prefix: str) -> Path:
        """Get cache file path"""
        return self.cache_dir / f"{prefix}_{key}.json"
    
    def get(self, key: str, prefix: str) -> Optional[Dict[str, Any]]:
        """Get cached data if available and not expired"""
        try:
            cache_path = self._get_cache_path(key, prefix)
            
            if not cache_path.exists():
                return None
            
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Check if cache is expired
            cached_at = datetime.fromisoformat(cache_data['cached_at'])
            if datetime.now() - cached_at > self.cache_ttl:
                logger.info(f"Cache expired for {prefix}:{key}")
                cache_path.unlink()  # Remove expired cache
                return None
            
            logger.info(f"Cache hit for {prefix}:{key}")
            return cache_data['data']
            
        except Exception as e:
            logger.error(f"Error getting cache: {str(e)}")
            return None
    
    def set(self, key: str, prefix: str, data: Dict[str, Any]) -> None:
        """Cache data with timestamp"""
        try:
            cache_path = self._get_cache_path(key, prefix)
            
            cache_data = {
                'cached_at': datetime.now().isoformat(),
                'data': data
            }
            
            def _serialize(obj):
                if hasattr(obj, 'isoformat'):
                    return obj.isoformat()
                raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2, default=_serialize)
            
            logger.info(f"Cached data for {prefix}:{key}")
            
        except Exception as e:
            logger.error(f"Error setting cache: {str(e)}")
    
    def clear(self, prefix: Optional[str] = None) -> None:
        """Clear cache files"""
        try:
            if prefix:
                cache_files = self.cache_dir.glob(f"{prefix}_*.json")
            else:
                cache_files = self.cache_dir.glob("*.json")
            
            for cache_file in cache_files:
                cache_file.unlink()
            
            logger.info(f"Cleared cache{' for ' + prefix if prefix else ''}")
            
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
