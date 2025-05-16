from fastapi import HTTPException
import redis.asyncio as redisasync
import redis.exceptions
from helpers.config import settings

redis_client = redisasync.from_url(settings.REDIS_URL, decode_responses=True)


async def get_redis_client() -> redisasync.Redis:
    """
    Dependency to get a Redis client.
    """
    return redis_client


async def close_redis_client(client: redisasync.Redis):
    """
    Dependency to close the Redis client.
    """
    await client.close()
    return client


async def get_redis_value(key: str) -> str:
    """
    Get a value from Redis by key.
    """
    try:
        value = await redis_client.get(key)
        if value is None:
            raise HTTPException(status_code=404, detail="Redis Key not found")
        return value
    except redis.exceptions.RedisError as e:
        raise HTTPException(status_code=500, detail=f"Redis error: {str(e)}")


async def set_redis_value(key: str, value: str, ex: int = 3600) -> bool:
    """
    Set a value in Redis with an expiration time.
    """
    try:
        await redis_client.setex(key, ex, value)
        return True
    except redis.exceptions.RedisError as e:
        raise HTTPException(status_code=500, detail=f"Redis error: {str(e)}")


async def delete_redis_value(key: str) -> bool:
    """
    Delete a value from Redis by key.
    """
    try:
        await redis_client.delete(key)
        return True
    except redis.exceptions.RedisError as e:
        raise HTTPException(status_code=500, detail=f"Redis error: {str(e)}")
