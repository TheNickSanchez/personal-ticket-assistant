import base64
import os
from typing import Dict, Any
import requests


class GitHubClient:
    """Simple GitHub API client for branch, commit, and PR creation."""

    def __init__(self, token: str | None = None, repo: str | None = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.repo = repo or os.getenv("GITHUB_REPO")
        if not self.token or not self.repo:
            raise ValueError("GitHub token and repo must be provided")
        self.api_base = "https://api.github.com"

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github+json",
        }

    def create_branch(self, branch: str, base: str = "main") -> Dict[str, Any]:
        """Create a branch from a base branch."""
        ref_url = f"{self.api_base}/repos/{self.repo}/git/refs/heads/{base}"
        resp = requests.get(ref_url, headers=self._headers())
        resp.raise_for_status()
        sha = resp.json()["object"]["sha"]

        create_url = f"{self.api_base}/repos/{self.repo}/git/refs"
        data = {"ref": f"refs/heads/{branch}", "sha": sha}
        resp = requests.post(create_url, headers=self._headers(), json=data)
        resp.raise_for_status()
        return resp.json()

    def create_commit(self, branch: str, path: str, content: str, message: str) -> Dict[str, Any]:
        """Create a commit by uploading file contents to a branch."""
        encoded = base64.b64encode(content.encode()).decode()
        url = f"{self.api_base}/repos/{self.repo}/contents/{path}"
        data = {
            "message": message,
            "content": encoded,
            "branch": branch,
        }
        resp = requests.put(url, headers=self._headers(), json=data)
        resp.raise_for_status()
        return resp.json()

    def create_pull_request(self, branch: str, title: str, body: str = "", base: str = "main") -> Dict[str, Any]:
        """Create a pull request from a branch."""
        url = f"{self.api_base}/repos/{self.repo}/pulls"
        data = {
            "title": title,
            "head": branch,
            "base": base,
            "body": body,
        }
        resp = requests.post(url, headers=self._headers(), json=data)
        resp.raise_for_status()
        return resp.json()
