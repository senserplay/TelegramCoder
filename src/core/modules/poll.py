from logging import Logger

from dishka import Provider, Scope, provide
from src.external.llm.proxy_api import ProxyAPI
from src.infrastructure.postgres.repositories.poll import PollDBGateWay
from src.infrastructure.postgres.repositories.poll_option import PollOptionDBGateWay
from src.infrastructure.redis.storages.poll import PollStorage
from src.services.code_line import CodeLineService
from src.services.poll import PollService
from src.services.poll_option import PollOptionService
from src.worker.poll import PollWorker


class PollProvider(Provider):
    def __init__(self, worker: PollWorker):
        super().__init__()
        self.worker = worker

    @provide(scope=Scope.REQUEST)
    def poll_service(
        self,
        poll_gateway: PollDBGateWay,
        poll_storage: PollStorage,
        poll_option_service: PollOptionService,
        code_line_service: CodeLineService,
        llm: ProxyAPI,
        logger: Logger,
    ) -> PollService:
        return PollService(
            poll_gateway, poll_storage, poll_option_service, code_line_service, llm, logger
        )

    @provide(scope=Scope.REQUEST)
    def poll_option_service(
        self, poll_option_gateway: PollOptionDBGateWay, logger: Logger
    ) -> PollOptionService:
        return PollOptionService(poll_option_gateway, logger)

    @provide(scope=Scope.APP)
    def poll_worker(self) -> PollWorker:
        return self.worker
