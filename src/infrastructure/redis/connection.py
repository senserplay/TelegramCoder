from redis import Redis
from src.core.config import env_settings


redis_client = Redis(
    host=env_settings.REDIS_HOST,
    port=env_settings.REDIS_PORT,
    username=env_settings.REDIS_USERNAME,
    db=int(env_settings.REDIS_DB_INDEX),
    password=env_settings.REDIS_PASSWORD,
)
