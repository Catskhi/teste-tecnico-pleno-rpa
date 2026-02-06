import json
import logging
import os
import uuid
from pathlib import Path
import httpx
from fastapi import FastAPI, HTTPException

from models import CrawlResponse, CrawlResult

logging.basicConfig(level=logging.INFO)
app = FastAPI(title="Crawler API")

OSCAR_SERVICE_URL = os.environ.get("OSCAR_SERVICE_URL", "http://oscar:8000")
DATA_DIR = Path(os.environ.get("DATA_DIR", "/app/data"))


@app.post("/crawl/oscar", response_model=CrawlResponse)
async def crawl_oscar():
    job_id = str(uuid.uuid4())

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"{OSCAR_SERVICE_URL}/scrape",
                json={"job_id": job_id},
            )
            response.raise_for_status()
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Oscar service unreachable: {exc}",
        )
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Oscar service error: {exc.response.status_code}",
        )

    return CrawlResponse(job_id=job_id, status="pending")


@app.get("/results/{job_id}", response_model=CrawlResult)
async def get_results(job_id: str):
    path = DATA_DIR / f"{job_id}.json"

    if not path.exists():
        raise HTTPException(status_code=404, detail="Job not found")

    data = json.loads(path.read_text())
    return CrawlResult(**data)
