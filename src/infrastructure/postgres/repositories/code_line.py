from typing import List

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.application.schemas.code_line import CodeLineCreateDTO, CodeLineResponseDTO
from src.infrastructure.postgres.models.code_line import CodeLine


class CodeLineDBGateWay:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_chat_code(self, chat_id: int) -> List[CodeLineResponseDTO]:
        result = await self.session.execute(select(CodeLine).where(CodeLine.chat_id == chat_id))
        code_lines: List[CodeLine] = list(result.scalars().all())
        return [CodeLineResponseDTO.model_validate(code_line.as_dict()) for code_line in code_lines]

    async def create_code_line(self, code_line_data: CodeLineCreateDTO) -> CodeLineResponseDTO:
        new_code_line = CodeLine(**code_line_data.model_dump())
        self.session.add(new_code_line)
        await self.session.commit()
        await self.session.refresh(new_code_line)

        return CodeLineResponseDTO.model_validate(new_code_line.as_dict())

    async def delete_chat_code(self, chat_id: int):
        stmt = delete(CodeLine).where(CodeLine.chat_id == chat_id)
        await self.session.execute(stmt)
        await self.session.commit()
