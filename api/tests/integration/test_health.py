"""Integration tests for health check endpoints."""

from fastapi.testclient import TestClient


def test_health_check(test_client: TestClient) -> None:
    """Test the health check endpoint."""
    response = test_client.get("/api/health")
    assert response.status_code == 200  # noqa: S101


def test_cors_middleware(test_client: TestClient) -> None:
    """Test CORS middleware is properly configured."""
    response = test_client.options(
        "/api/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200  # noqa: S101
    # FastAPI returns the specific origin instead of '*' when allow_credentials=True
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"  # noqa: S101
    assert "access-control-allow-credentials" in response.headers  # noqa: S101
    assert response.headers["access-control-allow-credentials"] == "true"  # noqa: S101
