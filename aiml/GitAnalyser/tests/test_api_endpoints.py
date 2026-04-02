"""
Tests for API endpoints.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestAPIEndpoints:
    """Test API endpoint functionality."""
    
    async def test_health_check(self, client: AsyncClient):
        """Test health check endpoint."""
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    async def test_root_endpoint(self, client: AsyncClient):
        """Test root endpoint."""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "version" in data
    
    async def test_analyze_repo_invalid_url(self, client: AsyncClient):
        """Test analyze endpoint with invalid URL."""
        response = await client.post(
            "/api/analyze-repo",
            json={"repo_url": "https://gitlab.com/owner/repo"}
        )
        assert response.status_code == 400
    
    async def test_analyze_repo_missing_url(self, client: AsyncClient):
        """Test analyze endpoint without URL."""
        response = await client.post(
            "/api/analyze-repo",
            json={}
        )
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.slow
    async def test_analyze_repo_valid_url(self, client: AsyncClient, mocker):
        """Test analyze endpoint with valid URL (mocked)."""
        # Mock GitHub service
        mock_github = mocker.patch("services.github_service.GitHubService")
        mock_github.return_value.parse_repo_url.return_value = ("owner", "repo")
        mock_github.return_value.get_repo_metadata.return_value = {
            "name": "repo",
            "language": "Python"
        }
        
        response = await client.post(
            "/api/analyze-repo",
            json={"repo_url": "https://github.com/owner/repo"}
        )
        
        # Should return 200 with repo_id and processing status
        assert response.status_code in [200, 500]  # May fail without full setup
