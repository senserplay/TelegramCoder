from aiogram.filters import BaseFilter
from aiogram.types import Message


class AdminOrPrivateFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        if message.chat.type == "private":
            return True

        if message.chat.type in ["group", "supergroup"]:
            try:
                admins = await message.bot.get_chat_administrators(message.chat.id)
                return message.from_user.id in [a.user.id for a in admins]
            except Exception:
                return False

        return False
