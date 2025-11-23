from logging import Logger
from typing import List

from src.application.schemas.code_line import CodeLineCreateDTO, CodeLineResponseDTO
from src.external.llm import prompt
from src.external.llm.proxy_api import ProxyAPI
from src.infrastructure.postgres.repositories.code_line import CodeLineDBGateWay


class CodeLineService:
    def __init__(
        self,
        code_line_gateway: CodeLineDBGateWay,
        llm: ProxyAPI,
        logger: Logger,
    ):
        self.code_line_gateway = code_line_gateway
        self.llm = llm
        self.logger = logger

    async def add_line(self, code_line_data: CodeLineCreateDTO) -> CodeLineResponseDTO:
        return await self.code_line_gateway.create_code_line(code_line_data)

    async def get_chat_code(self, chat_id: int) -> List[CodeLineResponseDTO]:
        return await self.code_line_gateway.get_chat_code(chat_id)

    async def code_complete(self, chat_id: int):
        last_code_lines = await self.get_chat_code(chat_id)
        poll_id = last_code_lines[0].poll_id
        completed_code_lines = self.llm.send_message(
            prompt.COMPLETE_PROMPT.format(last_code_lines=last_code_lines)
        )
        self.logger.info(f"COMPLETED CODE: {completed_code_lines}")
        await self.clear_chat_code(chat_id)
        for i, code_line in enumerate(completed_code_lines):
            code_line_data = CodeLineCreateDTO(
                chat_id=chat_id, poll_id=poll_id, line_number=i + 1, content=code_line
            )
            await self.add_line(code_line_data)
        return await self.get_chat_code(chat_id)

    async def clear_chat_code(self, chat_id: int):
        await self.code_line_gateway.delete_chat_code(chat_id)
