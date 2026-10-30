"""Load profile.toml, the hand-edited settings for the Open Source section."""

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RepoRef:
    repo: str  # "truera/trulens"
    name: str  # "TruLens"


@dataclass(frozen=True)
class ProjectConfig:
    repos: tuple[RepoRef, ...]
    description: str


@dataclass(frozen=True)
class ManualEntry:
    name: str
    label: str
    description: str
    count: str


@dataclass(frozen=True)
class Config:
    owner: str
    projects: tuple[ProjectConfig, ...]
    exclude_repos: frozenset[str]
    exclude_prs: frozenset[str]  # "owner/repo#123"
    manual: tuple[ManualEntry, ...]


def load_config(path: Path) -> Config:
    with open(path, "rb") as f:
        data = tomllib.load(f)
    projects = tuple(
        ProjectConfig(
            repos=tuple(RepoRef(repo=r["repo"], name=r["name"]) for r in p["repos"]),
            description=p["description"],
        )
        for p in data.get("project", [])
    )
    manual = tuple(
        ManualEntry(
            name=m["name"],
            label=m["label"],
            description=m["description"],
            count=m["count"],
        )
        for m in data.get("manual", [])
    )
    return Config(
        owner=data["owner"],
        projects=projects,
        exclude_repos=frozenset(data.get("exclude_repos", [])),
        exclude_prs=frozenset(data.get("exclude_prs", [])),
        manual=manual,
    )
