from logging import Logger
from typing import List

from src.application.schemas.code_line import CodeLineCreateDTO, CodeLineResponseDTO
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

    async def clear_chat_code(self, chat_id: int):
        await self.code_line_gateway.delete_chat_code(chat_id)
