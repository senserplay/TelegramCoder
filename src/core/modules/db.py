from typing import AsyncGenerator

from dishka import Provider, Scope, provide
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from src.infrastructure.postgres.repositories.chat import ChatDBGateWay
from src.infrastructure.postgres.repositories.code_line import CodeLineDBGateWay
from src.infrastructure.postgres.repositories.poll import PollDBGateWay
from src.infrastructure.postgres.repositories.poll_option import PollOptionDBGateWay


class DBProvider(Provider):
    def __init__(self, url: URL):
        super().__init__()

        self.DATABASE_URL = url
        self.SQLALCHEMY_CONNECT_ARGS = {
            "prepared_statement_cache_size": 500,
        }

    @provide(scope=Scope.REQUEST)
    async def get_connection(self) -> async_sessionmaker[AsyncSession]:
        engine = create_async_engine(
            self.DATABASE_URL,
            connect_args=self.SQLALCHEMY_CONNECT_ARGS,
            pool_size=30,
            max_overflow=50,
            pool_timeout=10,
            pool_recycle=1800,
            pool_pre_ping=True,
        )

        return async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    @provide(scope=Scope.REQUEST)
    async def db_session(
        self, connection: async_sessionmaker[AsyncSession]
    ) -> AsyncGenerator[AsyncSession, None]:
        async with connection() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    @provide(scope=Scope.REQUEST)
    async def chat_gateway(self, db_session: AsyncSession) -> ChatDBGateWay:
        return ChatDBGateWay(db_session)

    @provide(scope=Scope.REQUEST)
    async def poll_gateway(self, db_session: AsyncSession) -> PollDBGateWay:
        return PollDBGateWay(db_session)

    @provide(scope=Scope.REQUEST)
    async def poll_option_gateway(self, db_session: AsyncSession) -> PollOptionDBGateWay:
        return PollOptionDBGateWay(db_session)

    @provide(scope=Scope.REQUEST)
    async def code_line_gateway(self, db_session: AsyncSession) -> CodeLineDBGateWay:
        return CodeLineDBGateWay(db_session)
