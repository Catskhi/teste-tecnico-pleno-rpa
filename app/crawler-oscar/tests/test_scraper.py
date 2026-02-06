import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest
import respx

from models import CrawlResult, Film
from scraper import (
    DATA_DIR,
    TARGET_URL,
    YEARS,
    _save_result,
    crawl_oscar,
    fetch_year,
    fetch_year_http,
)

SAMPLE_FILMS_JSON = [
    {
        "title": "The King's Speech",
        "year": 2010,
        "awards": 4,
        "nominations": 12,
        "best_picture": True,
    },
    {
        "title": "Black Swan",
        "year": 2010,
        "awards": 1,
        "nominations": 5,
        "best_picture": False,
    },
]


@pytest.fixture
def tmp_data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr("scraper.DATA_DIR", tmp_path)
    return tmp_path


class TestFetchYearHttp:
    @pytest.mark.asyncio
    @respx.mock
    async def test_successful_fetch(self):
        respx.get(TARGET_URL, params={"ajax": "true", "year": "2010"}).mock(
            return_value=httpx.Response(200, json=SAMPLE_FILMS_JSON)
        )
        async with httpx.AsyncClient() as client:
            films = await fetch_year_http(client, 2010)

        assert len(films) == 2
        assert films[0].title == "The King's Speech"
        assert films[0].best_picture is True

    @pytest.mark.asyncio
    @respx.mock
    async def test_retries_on_failure_then_succeeds(self):
        route = respx.get(TARGET_URL, params={"ajax": "true", "year": "2010"})
        route.side_effect = [
            httpx.Response(500),
            httpx.Response(200, json=SAMPLE_FILMS_JSON),
        ]

        async with httpx.AsyncClient() as client:
            films = await fetch_year_http(client, 2010)

        assert len(films) == 2
        assert route.call_count == 2

    @pytest.mark.asyncio
    @respx.mock
    async def test_raises_after_max_retries(self):
        respx.get(TARGET_URL, params={"ajax": "true", "year": "2010"}).mock(
            return_value=httpx.Response(500)
        )
        async with httpx.AsyncClient() as client:
            with pytest.raises(httpx.HTTPStatusError):
                await fetch_year_http(client, 2010)


class TestFetchYear:
    @pytest.mark.asyncio
    @respx.mock
    async def test_uses_http_when_available(self):
        respx.get(TARGET_URL, params={"ajax": "true", "year": "2010"}).mock(
            return_value=httpx.Response(200, json=SAMPLE_FILMS_JSON)
        )
        async with httpx.AsyncClient() as client:
            films = await fetch_year(client, 2010)

        assert len(films) == 2

    @pytest.mark.asyncio
    @respx.mock
    async def test_falls_back_to_selenium(self):
        respx.get(TARGET_URL, params={"ajax": "true", "year": "2010"}).mock(
            return_value=httpx.Response(500)
        )
        mock_films = [
            Film(title="Film A", year=2010, awards=1, nominations=3),
        ]
        with patch("scraper.fetch_year_selenium", return_value=mock_films) as mock_sel:
            async with httpx.AsyncClient() as client:
                films = await fetch_year(client, 2010)

        assert len(films) == 1
        assert films[0].title == "Film A"
        mock_sel.assert_called_once_with(2010)


class TestSaveResult:
    def test_creates_json_file(self, tmp_data_dir):
        result = CrawlResult(job_id="save-test", status="completed")
        _save_result(result)

        path = tmp_data_dir / "save-test.json"
        assert path.exists()

        data = json.loads(path.read_text())
        assert data["job_id"] == "save-test"
        assert data["status"] == "completed"


class TestCrawlOscar:
    @pytest.mark.asyncio
    @respx.mock
    async def test_successful_crawl(self, tmp_data_dir):
        for year in YEARS:
            respx.get(TARGET_URL, params={"ajax": "true", "year": str(year)}).mock(
                return_value=httpx.Response(200, json=SAMPLE_FILMS_JSON)
            )

        result = await crawl_oscar("test-job")

        assert result.status == "completed"
        assert result.error is None
        assert len(result.films) == len(YEARS) * len(SAMPLE_FILMS_JSON)
        assert result.crawled_at is not None

        saved = tmp_data_dir / "test-job.json"
        assert saved.exists()

    @pytest.mark.asyncio
    @respx.mock
    async def test_partial_failure(self, tmp_data_dir):
        for year in YEARS:
            if year == 2010:
                respx.get(
                    TARGET_URL, params={"ajax": "true", "year": str(year)}
                ).mock(return_value=httpx.Response(500))
            else:
                respx.get(
                    TARGET_URL, params={"ajax": "true", "year": str(year)}
                ).mock(return_value=httpx.Response(200, json=SAMPLE_FILMS_JSON))

        with patch("scraper.fetch_year_selenium", side_effect=Exception("no browser")):
            result = await crawl_oscar("partial-job")

        assert result.status == "completed"
        assert "Partial failures" in result.error
        assert len(result.films) == (len(YEARS) - 1) * len(SAMPLE_FILMS_JSON)

    @pytest.mark.asyncio
    @respx.mock
    async def test_total_failure(self, tmp_data_dir):
        for year in YEARS:
            respx.get(TARGET_URL, params={"ajax": "true", "year": str(year)}).mock(
                return_value=httpx.Response(500)
            )

        with patch("scraper.fetch_year_selenium", side_effect=Exception("no browser")):
            result = await crawl_oscar("fail-job")

        assert result.status == "failed"
        assert result.error is not None
        assert result.films == []
