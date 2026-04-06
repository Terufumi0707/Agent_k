from pydantic import BaseModel, Field

from app.domain.enums.input_type import InputType


class CreateJobRequest(BaseModel):
    workflow_name: str = Field(default="meeting_minutes_generation")
    input_type: InputType
    audio_path: str | None = None
    transcript_text: str | None = None


class FeedbackRequest(BaseModel):
    target_version_no: int
    feedback_text: str


class ApproveRequest(BaseModel):
    target_version_no: int
