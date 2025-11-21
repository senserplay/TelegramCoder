from pydantic import BaseModel


class PollOptionResponseDTO(BaseModel):
    id: int
    poll_id: int
    option_index: int
    option_text: str
