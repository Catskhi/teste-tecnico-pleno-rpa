import logging

from fastapi import BackgroundTasks, FastAPI

logging.basicConfig(level=logging.INFO)
from pydantic import BaseModel

from scraper import crawl_oscar

app = FastAPI(title="Crawler Oscar")


class ScrapeRequest(BaseModel):
    job_id: str


class ScrapeResponse(BaseModel):
    job_id: str
    status: str


@app.post("/scrape", response_model=ScrapeResponse)
async def scrape(request: ScrapeRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(crawl_oscar, request.job_id)
    return ScrapeResponse(job_id=request.job_id, status="pending")
