import asyncio
import time
from datetime import datetime
from logging import Logger
from typing import Dict

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from src.application.schemas.code_line import CodeLineCreateDTO
from src.core.config import Settings
from src.external.llm.proxy_api import ProxyAPI
from src.infrastructure.postgres.connection import engine
from src.infrastructure.postgres.repositories.code_line import CodeLineDBGateWay
from src.infrastructure.postgres.repositories.poll import PollDBGateWay
from src.infrastructure.postgres.repositories.poll_option import PollOptionDBGateWay
from src.infrastructure.redis.connection import async_redis_client
from src.infrastructure.redis.storages.poll import PollStorage
from src.services.code_line import CodeLineService
from src.services.poll import PollService
from src.services.poll_option import PollOptionService


class PollWorker:
    def __init__(
        self,
        poll_storage: PollStorage,
        session_maker: async_sessionmaker[AsyncSession],
        llm: ProxyAPI,
        bot: Bot,
        logger: Logger,
        check_interval: int = 30,
    ):
        self.poll_storage = poll_storage
        self.session_maker = session_maker
        self.llm = llm
        self.bot = bot
        self.logger = logger
        self.check_interval = check_interval
        self._task = None

    async def start(self):
        self._task = asyncio.create_task(self._worker_loop())
        self.logger.info("🔄 Poll worker запущен")

    async def stop(self):
        if self._task:
            self._task.cancel()
            try:
                await self._task
                self.logger.info("⏹️ Poll worker остановлен")
            except asyncio.CancelledError:
                pass

    async def _worker_loop(self):
        self.logger.info(f"⚡ Poll worker запущен с интервалом {self.check_interval} секунд")
        while True:
            try:
                await self._process_expired_polls()
            except Exception as e:
                self.logger.error(f"🚨 Критическая ошибка в poll worker: {str(e)}")
            await asyncio.sleep(self.check_interval)

    async def _process_expired_polls(self):
        current_timestamp = int(time.time())
        self.logger.info(
            f"🔍 Проверка истекших опросов на {datetime.fromtimestamp(current_timestamp)}"
        )

        try:
            expired_chats = await self.poll_storage.get_expired_chats(current_timestamp)

            if not expired_chats:
                self.logger.info("✅ Нет истекших опросов для обработки")
                return

            self.logger.info(f"⏰ Найдено {len(expired_chats)} истекших опросов для обработки")

            for chat_id in expired_chats:
                try:
                    await self._process_expired_chat(chat_id, current_timestamp)
                except Exception as e:
                    self.logger.error(f"❌ Ошибка обработки чата {chat_id}: {str(e)}")

            self.logger.info("✅ Обработка истекших опросов завершена")

        except Exception as e:
            self.logger.error(f"❌ Ошибка в процессе проверки опросов: {str(e)}")

    async def _process_expired_chat(self, chat_id: int, current_timestamp: int):
        self.logger.info(f"🔧 Начало обработки чата {chat_id}")

        try:
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

            async with self.session_maker() as session:
                code_line_gateway = CodeLineDBGateWay(session)
                poll_option_gateway = PollOptionDBGateWay(session)
                poll_gateway = PollDBGateWay(session)

                code_line_service = CodeLineService(code_line_gateway, self.llm, self.logger)
                poll_option_service = PollOptionService(poll_option_gateway, self.logger)
                poll_service = PollService(
                    poll_gateway, self.poll_storage, poll_option_service, self.llm, self.logger
                )

                last_code_lines = await code_line_service.get_chat_code(chat_id)
                poll_option = await poll_option_service.get_poll_option(poll_id, winning_option)

                code_line_data = CodeLineCreateDTO(
                    chat_id=chat_id,
                    poll_id=poll_id,
                    line_number=len(last_code_lines) + 1,
                    content=poll_option.option_text,
                )
                await code_line_service.add_line(code_line_data)
                await self._cleanup_chat_data(chat_id, poll_id)

                new_poll_id = await poll_service.create_poll_for_chat(
                    chat_id=chat_id, bot=self.bot, last_code_lines=last_code_lines
                )

                self.logger.info(f"🆕 Создан новый опрос {new_poll_id} для чата {chat_id}")

            self.logger.info(f"✅ Обработка чата {chat_id} завершена успешно")

        except Exception as e:
            self.logger.error(f"❌ Критическая ошибка при обработке чата {chat_id}: {str(e)}")
            try:
                await self.poll_storage.clear_chat_data(chat_id)
            except Exception as cleanup_error:
                self.logger.error(
                    f"❌ Ошибка очистки данных для чата {chat_id}: {str(cleanup_error)}"
                )

    async def _get_vote_winner(self, votes: Dict[int, int]) -> int:
        if not votes:
            return 0

        winning_option = max(votes.items(), key=lambda x: x[1])[0]
        return winning_option

    async def _cleanup_chat_data(self, chat_id: int, poll_id: str):
        """Очистка данных чата после обработки"""
        self.logger.debug(f"🧹 Начало очистки данных для чата {chat_id}, опрос {poll_id}")

        try:
            await self.poll_storage.clear_poll_votes(poll_id)
            self.logger.debug(f"✅ Голоса для опроса {poll_id} очищены")

            await self.poll_storage.clear_chat_data(chat_id)
            self.logger.debug(f"✅ Данные активного опроса для чата {chat_id} очищены")

            next_poll_key = f"next_poll_at:{chat_id}"
            await self.poll_storage.redis_client.delete(next_poll_key)
            self.logger.debug(f"✅ Ключ времени следующего опроса для чата {chat_id} удален")

            self.logger.debug(f"✅ Все данные для чата {chat_id} успешно очищены")

        except Exception as e:
            self.logger.error(f"❌ Ошибка очистки данных для чата {chat_id}: {str(e)}")


def setup_poll_worker(
    config: Settings, logger: Logger, bot: Bot, check_interval: int = 30
) -> PollWorker:
    session_maker = async_sessionmaker(bind=engine, expire_on_commit=False)
    poll_storage = PollStorage(async_redis_client, logger)
    llm = ProxyAPI(config, logger)
    poll_worker = PollWorker(
        poll_storage=poll_storage,
        session_maker=session_maker,
        llm=llm,
        bot=bot,
        logger=logger,
        check_interval=check_interval,
    )
    return poll_worker
