from logging import Logger

from dishka import Provider, Scope, provide
from src.infrastructure.postgres.repositories.poll import PollDBGateWay
from src.infrastructure.postgres.repositories.poll_option import PollOptionDBGateWay
from src.infrastructure.redis.storages.poll import PollStorage
from src.services.poll import PollService
from src.services.poll_option import PollOptionService


class PollProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def poll_service(
        self,
        poll_gateway: PollDBGateWay,
        poll_storage: PollStorage,
        poll_option_service: PollOptionService,
        logger: Logger,
    ) -> PollService:
        return PollService(poll_gateway, poll_storage, poll_option_service, logger)

    @provide(scope=Scope.REQUEST)
    def poll_option_service(
        self, poll_option_gateway: PollOptionDBGateWay, logger: Logger
    ) -> PollOptionService:
        return PollOptionService(poll_option_gateway, logger)
