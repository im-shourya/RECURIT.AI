"""
GitHub service for fetching repository data.
Handles API interaction, rate limiting, and error handling.
"""
import httpx
import os
import re
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from services.cache_service import get_cache
from utils.logger import get_logger


class GitHubService:
    """Service for interacting with GitHub REST API."""
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        self.headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"
        
        self.cache = get_cache()
        self.logger = get_logger(__name__)
    
    def parse_repo_url(self, repo_url: str) -> Tuple[str, str]:
        """
        Parse GitHub repository URL to extract owner and repo name.
        Supports formats:
        - https://github.com/owner/repo
        - https://github.com/owner/repo.git
        - github.com/owner/repo
        """
        # Remove trailing slashes and .git
        repo_url = repo_url.rstrip('/').replace('.git', '')
        
        # Extract owner and repo using regex
        pattern = r'(?:https?://)?(?:www\.)?github\.com/([^/]+)/([^/]+)'
        match = re.search(pattern, repo_url)
        
        if not match:
            raise ValueError(f"Invalid GitHub repository URL: {repo_url}")
        
        owner = match.group(1)
        repo = match.group(2)
        
        return owner, repo
    
    async def get_repo_metadata(self, owner: str, repo: str) -> Dict:
        """Fetch repository metadata from GitHub API with caching."""
        cache_key = self.cache._generate_key("github:metadata", owner, repo)
        
        async def fetch():
            url = f"{self.BASE_URL}/repos/{owner}/{repo}"
            
            # Create client with SSL verification disabled for potential corporate proxies
            async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
                try:
                    self.logger.info("Fetching repo metadata", owner=owner, repo=repo)
                    response = await client.get(url, headers=self.headers)
                    response.raise_for_status()
                    return response.json()
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 404:
                        raise ValueError(f"Repository not found: {owner}/{repo}")
                    elif e.response.status_code == 403:
                        raise ValueError("GitHub API rate limit exceeded. Please add GITHUB_TOKEN to .env")
                    else:
                        raise ValueError(f"GitHub API error: {e.response.status_code}")
                except httpx.ConnectError as e:
                    raise ValueError(f"Failed to connect to GitHub: Connection error. Check your internet connection.")
                except httpx.TimeoutException as e:
                    raise ValueError(f"Failed to connect to GitHub: Request timed out. Check your internet connection.")
                except httpx.RequestError as e:
                    raise ValueError(f"Failed to connect to GitHub: {str(e)}")
        
        return await self.cache.get_or_fetch(cache_key, fetch, ttl=3600)
    
    async def get_readme(self, owner: str, repo: str) -> Optional[str]:
        """Fetch README content."""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/readme"
        
        async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
            try:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                
                # Fetch raw content
                if 'download_url' in data:
                    content_response = await client.get(data['download_url'])
                    content_response.raise_for_status()
                    return content_response.text
                return None
            except (httpx.HTTPStatusError, httpx.RequestError):
                return None
    
    async def get_file_content(self, owner: str, repo: str, path: str) -> Optional[str]:
        """Fetch content of a specific file."""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/contents/{path}"
        
        async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
            try:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                
                if isinstance(data, dict) and 'download_url' in data:
                    content_response = await client.get(data['download_url'])
                    content_response.raise_for_status()
                    return content_response.text
                return None
            except (httpx.HTTPStatusError, httpx.RequestError):
                return None
    
    async def list_files(self, owner: str, repo: str, path: str = "") -> List[Dict]:
        """List files in a directory."""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/contents/{path}"
        
        async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
            try:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                
                if isinstance(data, list):
                    return data
                return []
            except (httpx.HTTPStatusError, httpx.RequestError):
                return []
    
    async def get_issues(self, owner: str, repo: str, state: str = "open", max_issues: int = 50) -> List[Dict]:
        """Fetch repository issues."""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/issues"
        params = {
            "state": state,
            "per_page": min(max_issues, 100),
            "sort": "updated",
            "direction": "desc"
        }
        
        async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
            try:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                issues = response.json()
                
                # Filter out pull requests (they appear in issues endpoint)
                return [issue for issue in issues if 'pull_request' not in issue]
            except (httpx.HTTPStatusError, httpx.RequestError):
                return []
    
    async def get_repository_tree(self, owner: str, repo: str, branch: str = "main") -> List[Dict]:
        """
        Get repository file tree.
        Try main/master branches.
        """
        for branch_name in [branch, "main", "master"]:
            url = f"{self.BASE_URL}/repos/{owner}/{repo}/git/trees/{branch_name}?recursive=1"
            
            async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
                try:
                    response = await client.get(url, headers=self.headers)
                    response.raise_for_status()
                    data = response.json()
                    
                    if 'tree' in data:
                        return data['tree']
                except (httpx.HTTPStatusError, httpx.RequestError):
                    continue
        
        return []