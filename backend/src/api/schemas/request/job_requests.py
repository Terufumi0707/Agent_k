from pydantic import BaseModel, Field

from src.domain.models import InputType, ReviewAction


class StartJobRequest(BaseModel):
    input_type: InputType
    audio_path: str | None = None
    transcript: str | None = None


class ReviewRequest(BaseModel):
    selected_index: int = Field(ge=0)
    action: ReviewAction
    instruction: str | None = None
