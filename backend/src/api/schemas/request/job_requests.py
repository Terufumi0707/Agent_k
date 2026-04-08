from pydantic import BaseModel, Field

from src.domain.models import ReviewAction


class StartJobRequest(BaseModel):
    transcript: str | None = None


class ReviewRequest(BaseModel):
    selected_index: int = Field(ge=0)
    action: ReviewAction
    instruction: str | None = None
