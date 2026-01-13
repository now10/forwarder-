import asyncio
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

logger = logging.getLogger(__name__)

class FreeTierOptimizer:
    """Optimizations for Render free tier"""
    
    @staticmethod
    async def lightweight_db_session(db: AsyncSession):
        """Use lightweight database sessions"""
        # Set smaller pool size for free tier
        await db.execute("SET statement_timeout = 5000")  # 5 second timeout
        return db
    
    @staticmethod
    async def cache_with_timeout(redis: Optional[Redis], key: str, value: str, ttl: int = 300):
        """Cache with timeout, gracefully handle Redis downtime"""
        if not redis:
            return None
        
        try:
            await redis.setex(key, ttl, value)
            return True
        except Exception as e:
            logger.warning(f"Redis cache failed: {e}")
            return None
    
    @staticmethod
    def adjust_for_cold_start():
        """Adjust settings for cold starts"""
        import os
        if os.getenv("RENDER") and not os.getenv("WARM_START"):
            # We're in a cold start, be conservative
            logger.info("Cold start detected, using conservative settings")
            return {
                "db_pool_size": 1,
                "max_workers": 1,
                "timeout_multiplier": 2.0
            }
        return {
            "db_pool_size": 5,
            "max_workers": 4,
            "timeout_multiplier": 1.0
        }