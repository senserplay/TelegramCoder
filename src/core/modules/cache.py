from logging import Logger

from dishka import Provider, Scope, provide
from redis import Redis
from src.core.config import Settings
from src.infrastructure.redis.connection import redis_client
from src.infrastructure.redis.storages.poll import PollStorage


class CacheProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def get_connection(self) -> Redis:
        return redis_client

    @provide(scope=Scope.REQUEST)
    def poll_storage(self, redis_client: Redis, logger: Logger, config: Settings) -> PollStorage:
        return PollStorage(redis_client, logger, config.POLL_TTL)
