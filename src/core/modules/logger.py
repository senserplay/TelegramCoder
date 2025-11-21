import logging

from dishka import Provider, Scope, provide
from src.core.logging_setup import setup_logging


class LoggerProvider(Provider):
    @provide(scope=Scope.REQUEST)
    async def logger(self) -> logging.Logger:
        return setup_logging()
