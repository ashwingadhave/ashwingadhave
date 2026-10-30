"""Minimal GitHub REST client: PR search and repo details."""

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable

from profile_oss.collect import RepoInfo

API = "https://api.github.com"
PER_PAGE = 100


class GitHubError(RuntimeError):
    pass


class GitHubClient:
    def __init__(self, token: str, get_json: Callable[[str], tuple[int, Any]] | None = None):
        self._token = token
        self._get_json = get_json or self._urllib_get_json

    def _urllib_get_json(self, url: str) -> tuple[int, Any]:
        request = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {self._token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "profile-oss",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as e:
            try:
                body = json.load(e)
            except ValueError:
                body = {}
            return e.code, body
        except (urllib.error.URLError, TimeoutError) as e:
            raise GitHubError(f"network error for {url}: {e}") from e

    def _get(self, url: str) -> tuple[int, Any]:
        status, body = self._get_json(url)
        if status not in (200, 404):
            message = body.get("message", "") if isinstance(body, dict) else ""
            raise GitHubError(f"GitHub returned {status} for {url}: {message}")
        return status, body

    def search_prs(self, author: str) -> list[dict]:
        query = urllib.parse.quote(f"is:pr author:{author} -user:{author} is:public")
        items: list[dict] = []
        page = 1
        while True:
            url = f"{API}/search/issues?q={query}&per_page={PER_PAGE}&page={page}"
            status, body = self._get(url)
            if status == 404:
                raise GitHubError(f"search endpoint not found: {url}")
            batch = body.get("items", [])
            items.extend(batch)
            if len(batch) < PER_PAGE:
                return items
            page += 1

    def repo_info(self, full_name: str) -> RepoInfo | None:
        url = f"{API}/repos/{full_name}"
        status, body = self._get_json(url)
        message = body.get("message", "") if isinstance(body, dict) else ""
        # Deleted (404) or blocked (451, or a 403 that is not a rate limit): skip the repo.
        if status in (404, 451) or (status == 403 and "rate limit" not in message.lower()):
            return None
        if status != 200:
            raise GitHubError(f"GitHub returned {status} for {url}: {message}")
        return RepoInfo(
            full_name=body["full_name"],
            url=body["html_url"],
            stars=body["stargazers_count"],
            private=body["private"],
            description=body.get("description"),
        )
