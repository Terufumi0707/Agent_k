from typing import List, Optional

from pydantic import BaseModel, Field, model_validator


class OrderInfo(BaseModel):
    main_a_number: str
    backup_a_number: Optional[str] = None
    main_work_types: List[str]
    main_work_date: List[Optional[str]] = Field(default_factory=list)
    backup_work_types: List[str]
    backup_work_date: List[Optional[str]] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_work_dates(self) -> "OrderInfo":
        if len(self.main_work_date) != len(self.main_work_types):
            raise ValueError("main_work_date length must match main_work_types length")
        if len(self.backup_work_date) != len(self.backup_work_types):
            raise ValueError("backup_work_date length must match backup_work_types length")
        return self
