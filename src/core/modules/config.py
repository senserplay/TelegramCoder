from dishka import Provider, Scope, provide
from src.core.config import Settings


class ConfigProvider(Provider):
    @provide(scope=Scope.REQUEST)
    async def get_config(self) -> Settings:
        return Settings()
