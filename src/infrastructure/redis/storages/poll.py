from datetime import datetime, timedelta, timezone
from logging import Logger
from typing import Dict, List, Optional, Set

from redis.asyncio import Redis
from src.core.config import Settings


class PollStorage:
    def __init__(self, redis_client: Redis, logger: Logger, config: Settings):
        self.redis_client = redis_client
        self.logger = logger
        self.config = config

    async def set_active_poll(self, chat_id: int, poll_id: str) -> bool:
        key = f"active_poll:{chat_id}"
        return bool(await self.redis_client.set(key, poll_id))

    async def get_active_poll(self, chat_id: int) -> Optional[str]:
        key = f"active_poll:{chat_id}"
        poll_id = await self.redis_client.get(key)
        return poll_id

    async def clear_chat_data(self, chat_id: int) -> bool:
        active_poll_id = await self.get_active_poll(chat_id)
        if active_poll_id:
            await self.clear_poll_votes(active_poll_id)

        key = f"active_poll:{chat_id}"
        return bool(await self.redis_client.delete(key))

    async def add_vote(self, poll_id: str, user_id: int, option_index: int):
        key = f"poll_user_votes:{poll_id}"
        await self.redis_client.hset(key, str(user_id), str(option_index))

    async def get_poll_votes(self, poll_id: str) -> Dict[int, int]:
        key = f"poll_user_votes:{poll_id}"
        votes_data = await self.redis_client.hgetall(key)

        vote_counts = {}
        for user_id_str, option_str in votes_data.items():
            option = int(option_str)
            vote_counts[option] = vote_counts.get(option, 0) + 1

        return vote_counts

    async def get_total_votes(self, poll_id: str) -> int:
        key = f"poll_user_votes:{poll_id}"
        votes_data = await self.redis_client.hgetall(key)
        return len(votes_data)

    async def clear_poll_votes(self, poll_id: str) -> bool:
        key = f"poll_user_votes:{poll_id}"
        return bool(await self.redis_client.delete(key))

    async def set_next_poll_time(self, chat_id: int) -> datetime:
        current_time = datetime.now(timezone.utc)
        next_time = current_time + timedelta(seconds=self.config.POLL_TTL)
        timestamp = next_time.timestamp()

        key = f"next_poll_at:{chat_id}"
        await self.redis_client.set(key, str(timestamp))
        return next_time

    async def get_next_poll_time(self, chat_id: int) -> Optional[datetime]:
        key = f"next_poll_at:{chat_id}"
        timestamp_str = await self.redis_client.get(key)
        if not timestamp_str:
            return None

        return datetime.fromtimestamp(float(timestamp_str), tz=timezone.utc)

    async def clear_next_poll_time(self, chat_id: int):
        key = f"next_poll_at:{chat_id}"
        await self.redis_client.delete(key)

    async def get_expired_chats(self, current_timestamp: float) -> Set[int]:
        expired_chats = set()
        cursor = "0"

        while cursor != 0:
            cursor, keys = await self.redis_client.scan(
                cursor=int(cursor), match="next_poll_at:*", count=100
            )

            for key in keys:
                try:
                    chat_id = int(key.split(":")[1])
                    timestamp_str = await self.redis_client.get(key)

                    if timestamp_str:
                        timestamp = float(timestamp_str)
                        if timestamp <= current_timestamp:
                            expired_chats.add(chat_id)
                except (ValueError, TypeError, IndexError):
                    continue

        return expired_chats

    async def get_all_active_polls(self) -> List[str]:
        keys = await self.redis_client.keys("active_poll:*")
        if not keys:
            return []
        poll_ids = await self.redis_client.mget(keys)
        return [pid for pid in poll_ids if pid is not None and pid != ""]
