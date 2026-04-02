"""
Tests for GitHub service.
"""
import pytest
from services.github_service import GitHubService


class TestGitHubService:
    """Test GitHub service functionality."""
    
    def test_parse_repo_url_https(self):
        """Test parsing HTTPS GitHub URL."""
        service = GitHubService()
        owner, repo = service.parse_repo_url("https://github.com/owner/repo")
        assert owner == "owner"
        assert repo == "repo"
    
    def test_parse_repo_url_with_git(self):
        """Test parsing URL with .git extension."""
        service = GitHubService()
        owner, repo = service.parse_repo_url("https://github.com/owner/repo.git")
        assert owner == "owner"
        assert repo == "repo"
    
    def test_parse_repo_url_without_protocol(self):
        """Test parsing URL without protocol."""
        service = GitHubService()
        owner, repo = service.parse_repo_url("github.com/owner/repo")
        assert owner == "owner"
        assert repo == "repo"
    
    def test_parse_repo_url_invalid(self):
        """Test parsing invalid URL."""
        service = GitHubService()
        with pytest.raises(ValueError, match="Invalid GitHub repository URL"):
            service.parse_repo_url("https://gitlab.com/owner/repo")
    
    def test_parse_repo_url_with_trailing_slash(self):
        """Test parsing URL with trailing slash."""
        service = GitHubService()
        owner, repo = service.parse_repo_url("https://github.com/owner/repo/")
        assert owner == "owner"
        assert repo == "repo"
    
    @pytest.mark.asyncio
    async def test_get_repo_metadata_caching(self, mocker):
        """Test that metadata is cached."""
        service = GitHubService()
        
        # Mock the HTTP client
        mock_response = mocker.MagicMock()
        mock_response.json.return_value = {"name": "test-repo"}
        mock_response.raise_for_status = mocker.MagicMock()
        
        mock_client = mocker.MagicMock()
        mock_client.get = mocker.AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = mocker.AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = mocker.AsyncMock()
        
        mocker.patch("httpx.AsyncClient", return_value=mock_client)
        
        # First call should hit the API
        result1 = await service.get_repo_metadata("owner", "repo")
        assert result1["name"] == "test-repo"
        
        # Second call should use cache
        result2 = await service.get_repo_metadata("owner", "repo")
        assert result2["name"] == "test-repo"
        
        # HTTP client should only be called once
        assert mock_client.get.call_count == 1
