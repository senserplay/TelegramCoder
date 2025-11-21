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
        self.PROXY_API_KEY = os.getenv("PROXY_API_KEY")


env_settings = Settings()
