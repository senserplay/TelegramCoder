from dishka import Provider, Scope, provide
from src.infrastructure.redis.connection import redis_client
from src.infrastructure.redis.storages.poll import PollStorage


class PollStorageProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def get_poll_storage(self) -> PollStorage:
        return PollStorage(redis_client)
