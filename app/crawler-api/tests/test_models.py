import pytest
from pydantic import ValidationError

from models import CrawlResponse, CrawlResult, Film


class TestFilm:
    def test_valid_film(self):
        film = Film(
            title="The Artist",
            year=2011,
            awards=5,
            nominations=10,
            best_picture=True,
        )
        assert film.title == "The Artist"
        assert film.best_picture is True

    def test_defaults(self):
        film = Film(title="Test", year=2010, awards=1, nominations=2)
        assert film.best_picture is False


class TestCrawlResult:
    def test_valid_statuses(self):
        for status in ("pending", "running", "completed", "failed"):
            result = CrawlResult(job_id="x", status=status)
            assert result.status == status

    def test_invalid_status(self):
        with pytest.raises(ValidationError):
            CrawlResult(job_id="x", status="invalid")


class TestCrawlResponse:
    def test_crawl_response(self):
        resp = CrawlResponse(job_id="abc-123", status="pending")
        assert resp.job_id == "abc-123"
        assert resp.status == "pending"
