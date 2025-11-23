from sqlalchemy import inspect
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from src.core.config import config


class BaseWithAsDict:
    def as_dict(self):
        """
        Преобразует модель SQLAlchemy в словарь.
        """
        return {c.key: getattr(self, c.key) for c in inspect(self.__class__).columns}


Base = declarative_base(cls=BaseWithAsDict)

SQLALCHEMY_CONNECT_ARGS = {
    "prepared_statement_cache_size": 500,
}

DATABASE_URL = URL.create(
    "postgresql+asyncpg",
    username=config.PG_USERNAME,
    password=config.PG_PASSWORD,
    database=config.PG_DATABASE,
    host=config.PG_HOST,
    port=config.PG_PORT,
)

engine = create_async_engine(
    DATABASE_URL,
    connect_args=SQLALCHEMY_CONNECT_ARGS,
    pool_size=30,
    max_overflow=50,
    pool_timeout=10,
    pool_recycle=1800,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def get_db_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()
