from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.application.errors.http_errors.poll import PollAlreadyExistException, PollNotFoundException
from src.application.schemas.poll import PollCreateDTO, PollResponseDTO
from src.infrastructure.postgres.models.poll import Poll


class PollAlreadyExist:
    pass


class PollDBGateWay:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_poll(self, telegram_poll_id: int) -> PollResponseDTO:
        result = await self.session.execute(
            select(Poll).where(Poll.telegram_poll_id == telegram_poll_id)
        )
        poll: Poll = result.scalars().first()
        if poll is None:
            raise PollNotFoundException()
        return PollResponseDTO.model_validate(poll.as_dict())

    async def create_poll(self, poll_data: PollCreateDTO) -> PollResponseDTO:
        if self.is_exist(poll_data.telegram_poll_id):
            raise PollAlreadyExistException()
        new_poll = Poll(**poll_data.model_dump())
        self.session.add(new_poll)
        await self.session.commit()
        await self.session.refresh(new_poll)

        return await PollResponseDTO.model_validate(new_poll.as_dict())

    async def is_exist(self, telegram_poll_id: int) -> bool:
        result = await self.session.execute(
            select(Poll).where(Poll.telegram_poll_id == telegram_poll_id)
        )
        poll: Poll = result.scalars().first()
        return bool(poll)
