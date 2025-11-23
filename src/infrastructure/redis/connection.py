from redis.asyncio import Redis
from src.core.config import env_settings


async_redis_client = Redis(
    host=env_settings.REDIS_HOST,
    port=env_settings.REDIS_PORT,
    username=env_settings.REDIS_USERNAME,
    db=int(env_settings.REDIS_DB_INDEX),
    password=env_settings.REDIS_PASSWORD,
    decode_responses=True,
    socket_timeout=5.0,
    socket_connect_timeout=5.0,
    health_check_interval=30,
)
