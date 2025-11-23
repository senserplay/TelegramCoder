from aiogram.filters import BaseFilter
from aiogram.types import Message


class AdminFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        if message.chat.type in ["group", "supergroup"]:
            try:
                administrators = await message.bot.get_chat_administrators(message.chat.id)
                admin_user_ids = [admin.user.id for admin in administrators]
                return message.from_user.id in admin_user_ids
            except Exception:
                return True

        return False
