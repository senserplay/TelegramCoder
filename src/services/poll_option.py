from logging import Logger

from src.application.schemas.poll_option import PollOptionCreateDTO, PollOptionResponseDTO
from src.infrastructure.postgres.repositories.poll_option import PollOptionDBGateWay


class PollOptionService:
    def __init__(self, poll_option_gateway: PollOptionDBGateWay, logger: Logger):
        self.poll_option_gateway = poll_option_gateway
        self.logger = logger

    async def registration(self, poll_option_data: PollOptionCreateDTO) -> PollOptionResponseDTO:
        poll_option = await self.poll_option_gateway.create_poll_option(poll_option_data)
        self.logger.info(f"Вариант ответа зарегистрирован в БД, {poll_option.model_dump()}")
        return poll_option

    async def delete_chat_poll_options(self, chat_id: int):
        await self.poll_option_gateway.delete_chat_poll_options(chat_id)
