import logging

from dishka import Provider, Scope, provide
from src.core.log import logger


class LoggerProvider(Provider):
    @provide(scope=Scope.APP)
    async def get_logger(self) -> logging.Logger:
        return logger
