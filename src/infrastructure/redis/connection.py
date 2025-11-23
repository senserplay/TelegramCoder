from redis.asyncio import Redis
from src.core.config import config


async_redis_client = Redis(
    host=config.REDIS_HOST,
    port=config.REDIS_PORT,
    username=config.REDIS_USERNAME,
    db=int(config.REDIS_DB_INDEX),
    password=config.REDIS_PASSWORD,
    decode_responses=True,
    socket_timeout=5.0,
    socket_connect_timeout=5.0,
    health_check_interval=30,
)
