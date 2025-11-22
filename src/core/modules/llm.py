from logging import Logger

from dishka import Provider, Scope, provide
from src.core.config import Settings
from src.external.llm.proxy_api import ProxyAPI


class LLMProvider(Provider):
    @provide(scope=Scope.REQUEST)
    async def get_llm(self, config: Settings, logger: Logger) -> ProxyAPI:
        return ProxyAPI(config, logger)
