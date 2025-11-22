from logging import Logger

from aiogram.types import Message
from src.application.schemas.poll import PollCreateDTO, PollResponseDTO
from src.application.schemas.poll_option import PollOptionCreateDTO
from src.infrastructure.postgres.repositories.poll import PollDBGateWay
from src.infrastructure.redis.storages.poll import PollStorage
from src.services.poll_option import PollOptionService


class PollService:
    def __init__(
        self,
        poll_gateway: PollDBGateWay,
        poll_storage: PollStorage,
        poll_option_service: PollOptionService,
        logger: Logger,
    ):
        self.poll_gateway = poll_gateway
        self.poll_storage = poll_storage
        self.poll_option_service = poll_option_service
        self.logger = logger

    async def registration(self, message: Message) -> PollResponseDTO:
        poll_data = PollCreateDTO(
            chat_id=message.chat.id,
            telegram_poll_id=message.poll.id,
            question=message.poll.question,
        )
        poll = await self.poll_gateway.create_poll(poll_data)
        self.logger.info(f"Опрос зарегистрирован в БД, {poll.model_dump()}")
        options = []
        for option_index, option in enumerate(message.poll.options):
            poll_option_data = PollOptionCreateDTO(
                poll_id=poll.telegram_poll_id, option_index=option_index, option_text=option.text
            )
            await self.poll_option_service.registration(poll_option_data)
            options.append(option_index)

        self.poll_storage.set_active_poll(poll.chat_id, poll.telegram_poll_id)
        self.poll_storage.initialize_poll_votes(poll.telegram_poll_id, options)
        return poll

    async def clear_chat(self, message: Message):
        await self.poll_option_service.delete_chat_poll_options(message.chat.id)
        await self.poll_gateway.delete_chat_polls(message.chat.id)
        self.poll_storage.clear_chat_data(message.chat.id)
