from pydantic import BaseModel


class PollOptionResponseDTO(BaseModel):
    id: int
    poll_id: str
    option_index: int
    option_text: str


class PollOptionCreateDTO(BaseModel):
    poll_id: str
    option_index: int
    option_text: str
