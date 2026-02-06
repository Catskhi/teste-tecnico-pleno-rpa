import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import httpx
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from models import CrawlResult, Film

logger = logging.getLogger(__name__)

TARGET_URL = "https://www.scrapethissite.com/pages/ajax-javascript/"
YEARS = range(2010, 2016)
DATA_DIR = Path(os.environ.get("DATA_DIR", "/app/data"))
HTTP_TIMEOUT = 30
MAX_RETRIES = 3

async def fetch_year_http(client: httpx.AsyncClient, year: int) -> list[Film]:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = await client.get(
                TARGET_URL, params={"ajax": "true", "year": year}
            )
            response.raise_for_status()
            films = [Film(**item) for item in response.json()]
            logger.info("HTTP: fetched %d films for %d", len(films), year)
            return films
        except (httpx.HTTPStatusError, httpx.RequestError) as exc:
            logger.warning(
                "HTTP attempt %d/%d failed for %d: %s",
                attempt,
                MAX_RETRIES,
                year,
                exc,
            )
            if attempt == MAX_RETRIES:
                raise
            await asyncio.sleep(0.5 * attempt)
    return []

def _make_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")

    chrome_path = os.environ.get("CHROME_EXECUTABLE_PATH")
    if chrome_path:
        options.binary_location = chrome_path

    driver_path = os.environ.get("CHROMEDRIVER_PATH")
    service = Service(executable_path=driver_path) if driver_path else Service()

    return webdriver.Chrome(options=options, service=service)


def fetch_year_selenium(year: int) -> list[Film]:
    driver = _make_driver()
    try:
        driver.get(f"{TARGET_URL}?ajax=true&year={year}")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "pre"))
        )
        body = driver.find_element(By.TAG_NAME, "body").text
        films = [Film(**item) for item in json.loads(body)]
        logger.info("Selenium: fetched %d films for %d", len(films), year)
        return films
    finally:
        driver.quit()



async def fetch_year(client: httpx.AsyncClient, year: int) -> list[Film]:
    try:
        return await fetch_year_http(client, year)
    except Exception as exc:
        logger.warning(
            "HTTP failed for %d, falling back to Selenium: %s", year, exc
        )
        return await asyncio.to_thread(fetch_year_selenium, year)


def _save_result(result: CrawlResult) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / f"{result.job_id}.json"
    path.write_text(result.model_dump_json(indent=2))
    logger.info("Saved result to %s", path)


async def crawl_oscar(job_id: str) -> CrawlResult:
    logger.info("Starting crawl job %s", job_id)
    _save_result(CrawlResult(job_id=job_id, status="running"))

    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            year_results = await asyncio.gather(
                *[fetch_year(client, year) for year in YEARS],
                return_exceptions=True,
            )

        films: list[Film] = []
        errors: list[str] = []

        for year, year_result in zip(YEARS, year_results):
            if isinstance(year_result, Exception):
                errors.append(f"Year {year}: {year_result}")
                logger.error("Failed to collect year %d: %s", year, year_result)
            else:
                films.extend(year_result)

        if errors and not films:
            status = "failed"
            error_msg = "; ".join(errors)
        elif errors:
            status = "completed"
            error_msg = f"Partial failures: {'; '.join(errors)}"
        else:
            status = "completed"
            error_msg = None

        result = CrawlResult(
            job_id=job_id,
            status=status,
            films=films,
            crawled_at=datetime.now(timezone.utc),
            error=error_msg,
        )
    except Exception as exc:
        logger.exception("Crawl job %s failed unexpectedly", job_id)
        result = CrawlResult(
            job_id=job_id,
            status="failed",
            crawled_at=datetime.now(timezone.utc),
            error=str(exc),
        )

    _save_result(result)
    logger.info(
        "Crawl job %s finished: status=%s, films=%d",
        job_id,
        result.status,
        len(result.films),
    )
    return result
