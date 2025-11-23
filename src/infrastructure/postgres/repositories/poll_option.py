from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.application.errors.poll_option import (
    PollOptionAlreadyExistException,
    PollOptionNotFoundException,
)
from src.application.schemas.poll_option import PollOptionCreateDTO, PollOptionResponseDTO
from src.infrastructure.postgres.models.poll import Poll
from src.infrastructure.postgres.models.poll_option import PollOption


class PollOptionDBGateWay:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_poll_option(self, poll_id: str, option_index: int) -> PollOptionResponseDTO:
        result = await self.session.execute(
            select(PollOption).where(
                PollOption.poll_id == poll_id, PollOption.option_index == option_index
            )
        )
        poll_option: PollOption = result.scalars().first()
        if poll_option is None:
            raise PollOptionNotFoundException()
        return PollOptionResponseDTO.model_validate(poll_option.as_dict())

    async def create_poll_option(
        self, poll_option_data: PollOptionCreateDTO
    ) -> PollOptionResponseDTO:
        if await self.is_exist(poll_option_data):
            raise PollOptionAlreadyExistException()
        new_poll_option = PollOption(**poll_option_data.model_dump())
        self.session.add(new_poll_option)
        await self.session.commit()
        await self.session.refresh(new_poll_option)

        return PollOptionResponseDTO.model_validate(new_poll_option.as_dict())

    async def is_exist(self, poll_option_data: PollOptionCreateDTO) -> bool:
        result = await self.session.execute(
            select(PollOption).where(
                PollOption.poll_id == poll_option_data.poll_id,
                PollOption.option_index == poll_option_data.option_index,
            )
        )
        poll_option: PollOption = result.scalars().first()
        return bool(poll_option)

    async def delete_chat_poll_options(self, chat_id: int):
        await self.session.execute(
            delete(PollOption).where(
                PollOption.poll_id.in_(select(Poll.telegram_poll_id).where(Poll.chat_id == chat_id))
            )
        )
        await self.session.commit()
