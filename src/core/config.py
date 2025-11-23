import os

from dotenv import load_dotenv


class Settings:
    def __init__(self):
        load_dotenv()
        # Postgres Settings
        self.PG_HOST = os.getenv("PG_HOST")
        self.PG_PORT = int(os.getenv("PG_PORT"))
        self.PG_DATABASE = os.getenv("PG_DATABASE")
        self.PG_USERNAME = os.getenv("PG_USERNAME")
        self.PG_PASSWORD = os.getenv("PG_PASSWORD")

        # Redis Settings
        self.REDIS_HOST = os.getenv("REDIS_HOST")
        self.REDIS_PORT = int(os.getenv("REDIS_PORT"))
        self.REDIS_DB_INDEX = int(os.getenv("REDIS_DB_INDEX"))
        self.REDIS_USERNAME = os.getenv("REDIS_USERNAME")
        self.REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

        # Telegram Settings
        self.BOT_TOKEN = os.getenv("BOT_TOKEN")

        # AI Settings
        self.LLM_PROXY_API_KEY = os.getenv("LLM_PROXY_API_KEY")
        self.LLM_PROXY_BASE_URL = os.getenv("LLM_PROXY_BASE_URL")
        self.LLM_REQUEST_TIMEOUT = int(os.getenv("LLM_REQUEST_TIMEOUT"))
        self.LLM_MODEL = os.getenv("LLM_MODEL")

        # Poll Settings
        self.POLL_TTL = int(os.getenv("POLL_TTL"))
        self.WORKER_CHECK_INTERVAL = int(os.getenv("WORKER_CHECK_INTERVAL"))


config = Settings()
