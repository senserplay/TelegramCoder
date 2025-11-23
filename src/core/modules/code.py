from logging import Logger

from dishka import Provider, Scope, provide
from src.external.llm.proxy_api import ProxyAPI
from src.infrastructure.postgres.repositories.code_line import CodeLineDBGateWay
from src.services.code_line import CodeLineService


class CodeProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def code_line_service(
        self, code_line_gateway: CodeLineDBGateWay, llm: ProxyAPI, logger: Logger
    ) -> CodeLineService:
        return CodeLineService(code_line_gateway, llm, logger)
