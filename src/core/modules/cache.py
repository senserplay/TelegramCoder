from dishka import Provider, Scope, provide
from redis import Redis
from src.infrastructure.redis.connection import redis_client


class CacheProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def get_connection(self) -> Redis:
        return redis_client
