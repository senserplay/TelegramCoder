from logging import Logger
from typing import Dict, List, Optional

from aiogram import Bot
from aiogram.types import Message, PollOption
from src.application.schemas.code_line import CodeLineCreateDTO, CodeLineResponseDTO
from src.application.schemas.poll import PollCreateDTO, PollResponseDTO
from src.application.schemas.poll_option import PollOptionCreateDTO
from src.external.llm import prompt
from src.external.llm.proxy_api import ProxyAPI
from src.infrastructure.postgres.repositories.poll import PollDBGateWay
from src.infrastructure.redis.storages.poll import PollStorage
from src.services.code_line import CodeLineService
from src.services.poll_option import PollOptionService


class PollService:
    def __init__(
        self,
        poll_gateway: PollDBGateWay,
        poll_storage: PollStorage,
        poll_option_service: PollOptionService,
        code_line_service: CodeLineService,
        llm: ProxyAPI,
        logger: Logger,
    ):
        self.poll_gateway = poll_gateway
        self.poll_storage = poll_storage
        self.poll_option_service = poll_option_service
        self.code_line_service = code_line_service
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
        await self.poll_storage.set_next_poll_time(poll.chat_id)
        return poll

    async def generate_poll_options(
        self, chat_id: int, last_code_lines: Optional[List[CodeLineResponseDTO]] = None
    ):
        if last_code_lines is None:
            last_code_lines = []

        poll_options = self.llm.send_message(
            prompt.BASIC_PROMPT.format(
                last_code_lines=[code_line.content for code_line in last_code_lines]
            )
        )
        self.logger.info(f"Poll options: {poll_options}")

        if (
            not isinstance(poll_options, list)
            or len(poll_options) < 4
            or any(line == "" for line in poll_options)
        ):
            self.logger.error(f"Некорректный ответ от LLM для чата {chat_id}: {poll_options}")
            raise ValueError("Некорректный ответ от LLM для чата {chat_id}: {code_lines}")

        return poll_options

    async def create_poll_for_chat(
        self, chat_id: int, bot: Bot, last_code_lines: Optional[List[CodeLineResponseDTO]] = None
    ) -> str:
        poll_options = None
        while poll_options is None:
            try:
                poll_options = await self.generate_poll_options(chat_id, last_code_lines)
            except ValueError:
                continue

        question = "Выберите следующую строку программы:"
        poll_message = await bot.send_poll(
            chat_id=chat_id,
            question=question,
            options=poll_options[:4],
            is_anonymous=False,
            type="regular",
            allows_multiple_answers=False,
        )

        self.logger.info(f"Опрос создан для чата {chat_id}, poll_id={poll_message.poll.id}")

        await self.registration(chat_id, poll_message.poll.id, question, poll_message.poll.options)

        return poll_message.poll.id

    async def process_chat_poll(self, chat_id: int, bot: Bot):
        poll_id = await self.poll_storage.get_active_poll(chat_id)

        if not poll_id:
            self.logger.warning(
                f"⚠️ Нет активного опроса для чата {chat_id}, выполняем очистку данных"
            )
            await self.poll_storage.clear_chat_data(chat_id)
            return

        self.logger.info(f"📋 Найден активный опрос {poll_id} для чата {chat_id}")

        votes = await self.poll_storage.get_poll_votes(poll_id)

        if not votes:
            self.logger.warning(f"ℹ️ Нет голосов для опроса {poll_id} в чате {chat_id}")

        winning_option = await self._get_vote_winner(votes)

        last_code_lines = await self.code_line_service.get_chat_code(chat_id)
        poll_option = await self.poll_option_service.get_poll_option(poll_id, winning_option)

        code_line_data = CodeLineCreateDTO(
            chat_id=chat_id,
            poll_id=poll_id,
            line_number=len(last_code_lines) + 1,
            content=poll_option.option_text,
        )
        await self.code_line_service.add_line(code_line_data)
        await self.cleanup_chat_data(chat_id)

        new_poll_id = await self.create_poll_for_chat(
            chat_id=chat_id, bot=bot, last_code_lines=last_code_lines
        )

        self.logger.info(f"🆕 Создан новый опрос {new_poll_id} для чата {chat_id}")

    async def clear_chat(self, message: Message):
        await self.poll_option_service.delete_chat_poll_options(message.chat.id)
        await self.poll_gateway.delete_chat_polls(message.chat.id)
        await self.poll_storage.clear_chat_data(message.chat.id)

    async def cleanup_chat_data(self, chat_id: int):
        poll_id = await self.poll_storage.get_active_poll(chat_id)
        self.logger.debug(f"🧹 Начало очистки данных для чата {chat_id}, опрос {poll_id}")
        try:
            await self.poll_storage.clear_poll_votes(poll_id)
            self.logger.debug(f"✅ Голоса для опроса {poll_id} очищены")

            await self.poll_storage.clear_chat_data(chat_id)
            self.logger.debug(f"✅ Данные активного опроса для чата {chat_id} очищены")

            await self.poll_storage.clear_next_poll_time(chat_id)
            self.logger.debug(f"✅ Ключ времени следующего опроса для чата {chat_id} удален")

            self.logger.debug(f"✅ Все данные для чата {chat_id} успешно очищены")

        except Exception as e:
            self.logger.error(f"❌ Ошибка очистки данных для чата {chat_id}: {str(e)}")

    async def _get_vote_winner(self, votes: Dict[int, int]) -> int:
        if not votes:
            return 0

        winning_option = max(votes.items(), key=lambda x: x[1])[0]
        return winning_option
