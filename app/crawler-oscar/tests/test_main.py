from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class TestScrapeEndpoint:
    def test_scrape_returns_pending(self):
        with patch("main.crawl_oscar", new_callable=AsyncMock):
            response = client.post("/scrape", json={"job_id": "test-123"})

        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "test-123"
        assert data["status"] == "pending"

    def test_scrape_missing_job_id(self):
        response = client.post("/scrape", json={})
        assert response.status_code == 422
