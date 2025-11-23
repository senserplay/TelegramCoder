from logging import Logger
from typing import List

from aiogram import Bot
from aiogram.types import Message, PollOption
from src.application.schemas.poll import PollCreateDTO, PollResponseDTO
from src.application.schemas.poll_option import PollOptionCreateDTO
from src.external.llm import prompt
from src.external.llm.proxy_api import ProxyAPI
from src.infrastructure.postgres.repositories.poll import PollDBGateWay
from src.infrastructure.redis.storages.poll import PollStorage
from src.services.poll_option import PollOptionService


class PollService:
    def __init__(
        self,
        poll_gateway: PollDBGateWay,
        poll_storage: PollStorage,
        poll_option_service: PollOptionService,
        llm: ProxyAPI,
        logger: Logger,
    ):
        self.poll_gateway = poll_gateway
        self.poll_storage = poll_storage
        self.poll_option_service = poll_option_service
        self.llm = llm
        self.logger = logger

    async def registration(
        self, chat_id: int, telegram_poll_id: str, question: str, options_data: List[PollOption]
    ) -> PollResponseDTO:
        poll_data = PollCreateDTO(
            chat_id=chat_id,
            telegram_poll_id=telegram_poll_id,
            question=question,
        )
        poll = await self.poll_gateway.create_poll(poll_data)
        self.logger.info(f"Опрос зарегистрирован в БД, {poll.model_dump()}")
        options = []
        for option_index, option in enumerate(options_data):
            poll_option_data = PollOptionCreateDTO(
                poll_id=poll.telegram_poll_id, option_index=option_index, option_text=option.text
            )
            await self.poll_option_service.registration(poll_option_data)
            options.append(option_index)

        await self.poll_storage.set_active_poll(poll.chat_id, poll.telegram_poll_id)
        await self.poll_storage.set_next_poll_time(poll.chat_id, 10)
        return poll

    async def create_poll_for_chat(
        self, chat_id: int, bot: Bot, last_code_lines: list = None
    ) -> str:
        if last_code_lines is None:
            last_code_lines = []

        try:
            themes = self.llm.send_message(
                prompt.BASIC_PROMPT.format(last_code_lines=last_code_lines)
            )

            if not isinstance(themes, list) or len(themes) < 2:
                self.logger.error(f"Некорректный ответ от LLM для чата {chat_id}: {themes}")
                themes = [
                    "print('hello')",
                    "def main():",
                    "if __name__ == '__main__':",
                    "# TODO: implement",
                ]

            question = "Выберите следующую строку программы:"
            poll_message = await bot.send_poll(
                chat_id=chat_id,
                question=question,
                options=themes[:10],
                is_anonymous=False,
                type="regular",
                allows_multiple_answers=False,
            )

            self.logger.info(f"Опрос создан для чата {chat_id}, poll_id={poll_message.poll.id}")

            await self.registration(
                chat_id, poll_message.poll.id, question, poll_message.poll.options
            )

            return poll_message.poll.id

        except Exception as e:
            self.logger.error(f"Ошибка создания опроса для чата {chat_id}: {e}")
            raise

    async def clear_chat(self, message: Message):
        await self.poll_option_service.delete_chat_poll_options(message.chat.id)
        await self.poll_gateway.delete_chat_polls(message.chat.id)
        await self.poll_storage.clear_chat_data(message.chat.id)
