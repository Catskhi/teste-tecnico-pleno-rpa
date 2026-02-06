from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class Film(BaseModel):
    title: str
    year: int
    awards: int
    nominations: int
    best_picture: bool = False


class CrawlResult(BaseModel):
    job_id: str
    status: Literal["pending", "running", "completed", "failed"]
    films: list[Film] = []
    crawled_at: datetime | None = None
    error: str | None = None


class CrawlResponse(BaseModel):
    job_id: str
    status: str
