import pytest
from pydantic import ValidationError

from models import CrawlResult, Film


class TestFilm:
    def test_valid_film(self):
        film = Film(
            title="The King's Speech",
            year=2010,
            awards=4,
            nominations=12,
            best_picture=True,
        )
        assert film.title == "The King's Speech"
        assert film.year == 2010
        assert film.awards == 4
        assert film.nominations == 12
        assert film.best_picture is True

    def test_best_picture_defaults_false(self):
        film = Film(title="Inception", year=2010, awards=4, nominations=8)
        assert film.best_picture is False

    def test_strip_title_whitespace(self):
        film = Film(title="  Spotlight  ", year=2015, awards=2, nominations=6)
        assert film.title == "Spotlight"

    def test_missing_required_field_raises(self):
        with pytest.raises(ValidationError):
            Film(title="Test", year=2010, awards=1)

    def test_invalid_type_raises(self):
        with pytest.raises(ValidationError):
            Film(title="Test", year="not_a_number", awards=1, nominations=1)


class TestCrawlResult:
    def test_minimal_result(self):
        result = CrawlResult(job_id="abc-123", status="pending")
        assert result.job_id == "abc-123"
        assert result.status == "pending"
        assert result.films == []
        assert result.crawled_at is None
        assert result.error is None

    def test_invalid_status_raises(self):
        with pytest.raises(ValidationError):
            CrawlResult(job_id="abc", status="unknown")

    def test_result_with_films(self):
        films = [
            Film(title="Test Film", year=2010, awards=1, nominations=5),
        ]
        result = CrawlResult(job_id="abc", status="completed", films=films)
        assert len(result.films) == 1
        assert result.films[0].title == "Test Film"

    def test_json_round_trip(self):
        result = CrawlResult(
            job_id="test",
            status="completed",
            films=[Film(title="Film", year=2010, awards=1, nominations=2)],
        )
        json_str = result.model_dump_json()
        restored = CrawlResult.model_validate_json(json_str)
        assert restored == result
