from pydantic import BaseModel, Field, model_validator

from src.domain.models import InputType, ReviewAction


class StartJobRequest(BaseModel):
    input_type: InputType = InputType.TRANSCRIPT
    transcript: str | None = None
    audio_path: str | None = None

    @model_validator(mode="after")
    def validate_input(self) -> "StartJobRequest":
        if self.input_type == InputType.TRANSCRIPT and not (self.transcript or "").strip():
            raise ValueError("transcript is required")
        if self.input_type == InputType.AUDIO and not (self.audio_path or "").strip():
            raise ValueError("audio_path is required")
        return self


class ReviewRequest(BaseModel):
    selected_index: int = Field(ge=0)
    action: ReviewAction
    instruction: str | None = None
