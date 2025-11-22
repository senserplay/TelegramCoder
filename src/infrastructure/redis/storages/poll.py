from datetime import datetime, timedelta, timezone
from logging import Logger
from typing import Dict, Optional, Tuple, Union

import redis
from redis.exceptions import RedisError


class PollStorage:
    def __init__(self, redis_client: redis.Redis, logger: Logger):
        self.redis_client = redis_client
        self.logger = logger

    def set_active_poll(self, chat_id: int, poll_id: int) -> bool:
        try:
            key = f"active_poll:{chat_id}"
            result = self.redis_client.set(key, str(poll_id))
            self.logger.debug(f"Установлен активный опрос {poll_id} для чата {chat_id}")
            return bool(result)
        except RedisError as e:
            self.logger.error(f"Ошибка установки активного опроса для чата {chat_id}: {str(e)}")
            raise

    def get_active_poll(self, chat_id: int) -> Optional[int]:
        try:
            key = f"active_poll:{chat_id}"
            poll_id_bytes = self.redis_client.get(key)
            if poll_id_bytes:
                return int(poll_id_bytes.decode("utf-8"))
            return None
        except RedisError as e:
            self.logger.error(f"Ошибка получения активного опроса для чата {chat_id}: {str(e)}")
            raise

    def clear_active_poll(self, chat_id: int) -> bool:
        try:
            key = f"active_poll:{chat_id}"
            result = self.redis_client.delete(key)
            self.logger.debug(f"Очищен активный опрос для чата {chat_id}")
            return bool(result)
        except RedisError as e:
            self.logger.error(f"Ошибка очистки активного опроса для чата {chat_id}: {str(e)}")
            raise

    def initialize_poll_votes(self, poll_id: int, option_count: int) -> bool:
        try:
            key = f"poll_live_votes:{poll_id}"
            pipe = self.redis_client.pipeline()

            for option_index in range(option_count):
                # Используем строковые ключи и значения для хеша
                pipe.hset(key, str(option_index), "0")

            pipe.expire(key, 86400)  # 24 часа

            results = pipe.execute()
            self.logger.debug(
                f"Инициализированы голоса для опроса {poll_id} с {option_count} вариантами"
            )
            # Проверяем все hset операции (кроме последней - expire)
            return all(result == 1 for result in results[:-1])
        except RedisError as e:
            self.logger.error(f"Ошибка инициализации голосов для опроса {poll_id}: {str(e)}")
            raise

    def add_vote(self, poll_id: int, option_index: int) -> Tuple[bool, int]:
        try:
            key = f"poll_live_votes:{poll_id}"
            new_count = self.redis_client.hincrby(key, str(option_index), 1)
            self.logger.debug(
                f"Добавлен голос за вариант {option_index} в опросе {poll_id}. Новое значение: {new_count}"
            )
            return True, int(new_count)
        except RedisError as e:
            self.logger.error(
                f"Ошибка добавления голоса для опроса {poll_id}, вариант {option_index}: {str(e)}"
            )
            raise

    def get_poll_votes(self, poll_id: int) -> Dict[int, int]:
        try:
            key = f"poll_live_votes:{poll_id}"
            votes_data = self.redis_client.hgetall(key)

            if not votes_data:
                self.logger.warning(f"Не найдены данные голосов для опроса {poll_id}")
                return {}

            return {
                int(opt_idx.decode("utf-8")): int(count.decode("utf-8"))
                for opt_idx, count in votes_data.items()
            }
        except RedisError as e:
            self.logger.error(f"Ошибка получения голосов для опроса {poll_id}: {str(e)}")
            raise

    def get_total_votes(self, poll_id: int) -> int:
        try:
            votes = self.get_poll_votes(poll_id)
            return sum(votes.values())
        except RedisError as e:
            self.logger.error(
                f"Ошибка получения общего количества голосов для опроса {poll_id}: {str(e)}"
            )
            raise

    def set_next_poll_time(self, chat_id: int, delay_minutes: int = 60) -> datetime:
        try:
            # Используем timezone-aware datetime
            current_time = datetime.now(timezone.utc)
            next_time = current_time + timedelta(minutes=delay_minutes)
            timestamp = next_time.timestamp()

            key = f"next_poll_at:{chat_id}"
            self.redis_client.set(key, str(timestamp))

            self.logger.debug(
                f"Установлено время следующего опроса для чата {chat_id}: {next_time.isoformat()}"
            )
            return next_time
        except RedisError as e:
            self.logger.error(
                f"Ошибка установки времени следующего опроса для чата {chat_id}: {str(e)}"
            )
            raise

    def get_next_poll_time(self, chat_id: int) -> Optional[datetime]:
        try:
            key = f"next_poll_at:{chat_id}"
            timestamp_bytes = self.redis_client.get(key)

            if not timestamp_bytes:
                return None

            timestamp_str = timestamp_bytes.decode("utf-8")
            timestamp = float(timestamp_str)
            return datetime.fromtimestamp(timestamp, tz=timezone.utc)
        except RedisError as e:
            self.logger.error(
                f"Ошибка получения времени следующего опроса для чата {chat_id}: {str(e)}"
            )
            raise
        except (ValueError, TypeError) as e:
            self.logger.error(f"Ошибка парсинга времени для чата {chat_id}: {str(e)}")
            return None

    def is_poll_time_expired(self, chat_id: int) -> bool:
        try:
            next_poll_time = self.get_next_poll_time(chat_id)
            if not next_poll_time:
                return True

            current_time = datetime.now(timezone.utc)
            return current_time >= next_poll_time
        except RedisError as e:
            self.logger.error(f"Ошибка проверки времени опроса для чата {chat_id}: {str(e)}")
            raise

    def cleanup_poll_data(self, chat_id: int, poll_id: int) -> bool:
        try:
            pipe = self.redis_client.pipeline()

            pipe.delete(f"active_poll:{chat_id}")
            pipe.delete(f"poll_live_votes:{poll_id}")
            pipe.delete(f"next_poll_at:{chat_id}")

            results = pipe.execute()
            self.logger.info(f"Очищены данные опроса {poll_id} для чата {chat_id}")
            return all(results)
        except RedisError as e:
            self.logger.error(
                f"Ошибка очистки данных опроса {poll_id} для чата {chat_id}: {str(e)}"
            )
            raise

    def get_poll_results(self, poll_id: int) -> Dict[str, Union[int, Dict[int, int]]]:
        try:
            votes = self.get_poll_votes(poll_id)
            total_votes = sum(votes.values())

            return {"total_votes": total_votes, "votes_by_option": votes}
        except RedisError as e:
            self.logger.error(f"Ошибка получения результатов опроса {poll_id}: {str(e)}")
            raise
