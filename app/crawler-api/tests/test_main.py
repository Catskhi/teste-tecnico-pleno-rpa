import json

import httpx
import respx
from fastapi.testclient import TestClient

from main import OSCAR_SERVICE_URL, app

client = TestClient(app)


class TestCrawlOscarEndpoint:
    @respx.mock
    def test_triggers_crawl_returns_job_id(self):
        respx.post(f"{OSCAR_SERVICE_URL}/scrape").mock(
            return_value=httpx.Response(200, json={"job_id": "x", "status": "pending"})
        )

        response = client.post("/crawl/oscar")

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "pending"

    @respx.mock
    def test_returns_502_when_oscar_unreachable(self):
        respx.post(f"{OSCAR_SERVICE_URL}/scrape").mock(
            side_effect=httpx.ConnectError("Connection refused")
        )

        response = client.post("/crawl/oscar")
        assert response.status_code == 502

    @respx.mock
    def test_returns_502_on_oscar_error(self):
        respx.post(f"{OSCAR_SERVICE_URL}/scrape").mock(return_value=httpx.Response(500))

        response = client.post("/crawl/oscar")
        assert response.status_code == 502


class TestGetResultsEndpoint:
    def test_returns_404_for_missing_job(self, tmp_path, monkeypatch):
        monkeypatch.setattr("main.DATA_DIR", tmp_path)

        response = client.get("/results/nonexistent")
        assert response.status_code == 404

    def test_rejects_path_traversal(self, tmp_path, monkeypatch):
        monkeypatch.setattr("main.DATA_DIR", tmp_path)

        response = client.get("/results/..")
        assert response.status_code in (400, 404)

    def test_returns_result_from_json(self, tmp_path, monkeypatch):
        monkeypatch.setattr("main.DATA_DIR", tmp_path)

        result = {
            "job_id": "test-id",
            "status": "completed",
            "films": [
                {
                    "title": "The Artist",
                    "year": 2011,
                    "awards": 5,
                    "nominations": 10,
                    "best_picture": True,
                }
            ],
            "crawled_at": "2025-01-01T00:00:00Z",
            "error": None,
        }
        (tmp_path / "test-id.json").write_text(json.dumps(result))

        response = client.get("/results/test-id")

        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "test-id"
        assert data["status"] == "completed"
        assert len(data["films"]) == 1
        assert data["films"][0]["title"] == "The Artist"
