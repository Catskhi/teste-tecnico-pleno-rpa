from datetime import datetime
from typing import Literal

from pydantic import BaseModel, field_validator


class Film(BaseModel):
    title: str
    year: int
    awards: int
    nominations: int
    best_picture: bool = False

    @field_validator("title")
    @classmethod
    def strip_title(cls, v: str) -> str:
        return v.strip()


class CrawlResult(BaseModel):
    job_id: str
    status: Literal["pending", "running", "completed", "failed"]
    films: list[Film] = []
    crawled_at: datetime | None = None
    error: str | None = None
