from pydantic import BaseModel
from typing import Optional


class SubmissionCreate(BaseModel):
    username: str
    # Additional fields can be added as needed


class SubmissionOut(BaseModel):
    id: int
    username: str
    score: Optional[float]
    filename: Optional[str]

    class Config:
        orm_mode = True
