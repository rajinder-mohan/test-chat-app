from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
import aioredis
from typing import Optional, Any
import hashlib
import json

from app.config import settings

class CacheService:
    @staticmethod
    async def setup_cache():
        """Initialize cache when application starts."""
        if settings.REDIS_URL:
            redis = aioredis.from_url(settings.REDIS_URL, encoding="utf8", decode_responses=True)
            FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
    
    @staticmethod
    def get_cache_key(func_name: str, *args, **kwargs) -> str:
        """Generate a cache key for the given function and arguments."""
        # Convert all arguments to a string representation
        args_str = json.dumps(args, sort_keys=True)
        kwargs_str = json.dumps(kwargs, sort_keys=True)
        
        # Generate a hash from the function name and arguments
        key = f"{func_name}:{args_str}:{kwargs_str}"
        return hashlib.md5(key.encode()).hexdigest()
    
    @staticmethod
    def cache_response(expire: Optional[int] = None):
        """Decorator to cache function responses."""
        if not expire:
            expire = settings.CACHE_EXPIRE_SECONDS
        
        return cache(expire=expire) 