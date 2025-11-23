import asyncio
import time
from datetime import datetime
from logging import Logger

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
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
        self._running = False
        self._last_check_time = None

    async def start(self):
        self._task = asyncio.create_task(self._worker_loop())
        self._running = True
        self.logger.info("🔄 Poll worker запущен")

    async def stop(self):
        if self._task:
            self._task.cancel()
            try:
                await self._task
                self._running = False
                self.logger.info("⏹️ Poll worker остановлен")
            except asyncio.CancelledError:
                pass

    async def _worker_loop(self):
        self.logger.info(f"⚡ Poll worker запущен с интервалом {self.check_interval} секунд")
        while True:
            try:
                await self._process_expired_polls()
                self._last_check_time = time.time()
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
                    await self._process_expired_chat(chat_id)
                except Exception as e:
                    self.logger.error(f"❌ Ошибка обработки чата {chat_id}: {str(e)}")

            self.logger.info("✅ Обработка истекших опросов завершена")

        except Exception as e:
            self.logger.error(f"❌ Ошибка в процессе проверки опросов: {str(e)}")

    async def _process_expired_chat(self, chat_id: int):
        self.logger.info(f"🔧 Начало обработки чата {chat_id}")

        try:
            async with self.session_maker() as session:
                poll_gateway = PollDBGateWay(session)
                poll_option_gateway = PollOptionDBGateWay(session)
                code_line_gateway = CodeLineDBGateWay(session)

                poll_option_service = PollOptionService(poll_option_gateway, self.logger)
                code_line_service = CodeLineService(code_line_gateway, self.llm, self.logger)
                poll_service = PollService(
                    poll_gateway,
                    self.poll_storage,
                    poll_option_service,
                    code_line_service,
                    self.llm,
                    self.logger,
                )
                await poll_service.process_chat_poll(chat_id, self.bot)

            self.logger.info(f"✅ Обработка чата {chat_id} завершена успешно")

        except Exception as e:
            self.logger.error(f"❌ Критическая ошибка при обработке чата {chat_id}: {str(e)}")
            try:
                await self.poll_storage.clear_chat_data(chat_id)
            except Exception as cleanup_error:
                self.logger.error(
                    f"❌ Ошибка очистки данных для чата {chat_id}: {str(cleanup_error)}"
                )

    async def get_status(self) -> dict:
        now = time.time()
        if not self._running:
            return {"status": "stopped", "last_check_ago": None}
        if self._last_check_time is None:
            return {"status": "running", "last_check_ago": None}
        return {
            "status": "running",
            "last_check_ago": int(now - self._last_check_time),
            "check_interval": self.check_interval,
        }


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
