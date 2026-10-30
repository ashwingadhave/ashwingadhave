"""Turn raw GitHub search results into the PRs the profile should show."""

from dataclasses import dataclass
from datetime import date
from typing import Literal

from profile_oss.config import Config


@dataclass(frozen=True)
class RepoInfo:
    full_name: str
    url: str
    stars: int
    private: bool
    description: str | None


@dataclass(frozen=True)
class PR:
    repo: str
    number: int
    title: str
    url: str
    status: Literal["merged", "in_review"]
    when: date  # merged date for merged PRs, opened date for PRs in review


def repo_from_api_url(repository_url: str) -> str:
    owner, name = repository_url.rstrip("/").split("/")[-2:]
    return f"{owner}/{name}"


def repos_in(items: list[dict]) -> set[str]:
    return {repo_from_api_url(item["repository_url"]) for item in items}


def _status(item: dict) -> Literal["merged", "in_review"] | None:
    if (item.get("pull_request") or {}).get("merged_at"):
        return "merged"
    if item["state"] == "open" and not item.get("draft"):
        return "in_review"
    return None  # draft, or closed without merging


def select_prs(
    items: list[dict], repos: dict[str, RepoInfo | None], config: Config
) -> list[PR]:
    owner = config.owner.lower()
    prs = []
    for item in items:
        repo = repo_from_api_url(item["repository_url"])
        if repo.split("/")[0].lower() == owner:
            continue
        if repo in config.exclude_repos or f"{repo}#{item['number']}" in config.exclude_prs:
            continue
        info = repos.get(repo)
        if info is None or info.private:
            continue
        status = _status(item)
        if status is None:
            continue
        stamp = item["pull_request"]["merged_at"] if status == "merged" else item["created_at"]
        prs.append(
            PR(
                repo=repo,
                number=item["number"],
                title=item["title"],
                url=item["html_url"],
                status=status,
                when=date.fromisoformat(stamp[:10]),
            )
        )
    return prs
