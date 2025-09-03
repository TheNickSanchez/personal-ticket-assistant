import base64
from unittest.mock import patch

import pytest

from integrations.github_client import GitHubClient


class MockResponse:
    def __init__(self, json_data, status_code=200):
        self._json = json_data
        self.status_code = status_code

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


def test_create_branch_makes_api_calls():
    client = GitHubClient(token="t", repo="me/repo")
    with patch("requests.get") as mock_get, patch("requests.post") as mock_post:
        mock_get.return_value = MockResponse({"object": {"sha": "abc"}})
        mock_post.return_value = MockResponse({"ref": "refs/heads/feature"}, 201)
        result = client.create_branch("feature")
        assert mock_get.call_args[0][0].endswith("/git/refs/heads/main")
        assert mock_post.call_args[1]["json"] == {"ref": "refs/heads/feature", "sha": "abc"}
        assert result["ref"] == "refs/heads/feature"


def test_create_commit_uploads_content():
    client = GitHubClient(token="t", repo="me/repo")
    with patch("requests.put") as mock_put:
        mock_put.return_value = MockResponse({"content": {}})
        client.create_commit("feature", "file.txt", "hello", "msg")
        args, kwargs = mock_put.call_args
        assert args[0].endswith("/repos/me/repo/contents/file.txt")
        data = kwargs["json"]
        assert data["branch"] == "feature"
        assert data["message"] == "msg"
        assert data["content"] == "aGVsbG8="


def test_create_pull_request_posts_to_api():
    client = GitHubClient(token="t", repo="me/repo")
    with patch("requests.post") as mock_post:
        mock_post.return_value = MockResponse({"html_url": "url"}, 201)
        pr = client.create_pull_request("feature", "title", "body")
        assert mock_post.call_args[0][0].endswith("/repos/me/repo/pulls")
        assert mock_post.call_args[1]["json"]["head"] == "feature"
        assert pr["html_url"] == "url"
