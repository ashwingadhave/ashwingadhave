"""Render the Open Source section: one quiet line per project, PRs folded below."""

import re
from dataclasses import dataclass
from datetime import date

from profile_oss.collect import PR, RepoInfo
from profile_oss.config import Config, ManualEntry

_PREFIX = re.compile(
    r"^(feat|fix|docs|chore|refactor|test|tests|perf|build|ci|style|revert)(\([^)]*\))?!?:\s*",
    re.IGNORECASE,
)
_SENTENCE_END = re.compile(r"(?<=[.!?])\s")


@dataclass(frozen=True)
class Project:
    links: tuple[tuple[str, str, int], ...]  # (display name, repo url, stars)
    description: str
    prs: tuple[PR, ...]
    top_stars: int


def format_stars(n: int) -> str:
    if n < 1000:
        return f"{n}★"
    return f"{n / 1000:.1f}".rstrip("0").rstrip(".") + "k★"


def clean_title(title: str) -> str:
    cleaned = _PREFIX.sub("", title, count=1)
    return cleaned or title


def _first_sentence(text: str | None) -> str:
    if not text:
        return ""
    return _SENTENCE_END.split(text.strip(), maxsplit=1)[0]


def _escape(text: str) -> str:
    for ch in "\\[]|`*":
        text = text.replace(ch, "\\" + ch)
    return text.replace("<", "&lt;").replace(">", "&gt;")


def _sentence(text: str) -> str:
    return text if text.endswith((".", "!", "?")) else text + "."


def build_projects(
    prs: list[PR], repos: dict[str, RepoInfo | None], config: Config
) -> list[Project]:
    by_repo: dict[str, list[PR]] = {}
    for pr in prs:
        by_repo.setdefault(pr.repo, []).append(pr)

    def make(refs: list[tuple[str, str]], description: str) -> Project:
        infos = [(name, repos[repo]) for repo, name in refs]
        project_prs = [pr for repo, _ in refs for pr in by_repo[repo]]
        return Project(
            links=tuple((name, info.url, info.stars) for name, info in infos),
            description=description,
            prs=tuple(sorted(project_prs, key=lambda pr: pr.when, reverse=True)),
            top_stars=max(info.stars for _, info in infos),
        )

    projects = []
    configured = set()
    for pc in config.projects:
        refs = [(ref.repo, ref.name) for ref in pc.repos if ref.repo in by_repo]
        configured.update(ref.repo for ref in pc.repos)
        if refs:
            projects.append(make(refs, pc.description))
    for repo in by_repo:
        if repo not in configured:
            # Name and description come from someone else's repo, so escape them.
            info = repos[repo]
            projects.append(
                make([(repo, _escape(repo.split("/")[1]))], _escape(_first_sentence(info.description)))
            )

    def project_name(p: Project) -> str:
        return " · ".join(name for name, _, _ in p.links)

    return sorted(projects, key=lambda p: (-p.top_stars, project_name(p).lower()))


def _counts(prs: tuple[PR, ...]) -> str:
    merged = sum(pr.status == "merged" for pr in prs)
    in_review = len(prs) - merged
    parts = []
    if merged:
        parts.append(f"{merged} merged")
    if in_review:
        parts.append(f"{in_review} in review")
    return " · ".join(parts)


def _pr_line(pr: PR) -> str:
    status = f"merged {pr.when:%b %Y}" if pr.status == "merged" else "in review"
    return f"- [{_escape(clean_title(pr.title))}]({pr.url}) — {status}"


def _project_block(p: Project) -> str:
    names = " · ".join(
        f"**[{name}]({url})** <sub>{format_stars(stars)}</sub>" for name, url, stars in p.links
    )
    description = f" — {_sentence(p.description)}" if p.description else ""
    count = len(p.prs)
    summary = f"{count} pull request" + ("" if count == 1 else "s")
    lines = "\n".join(_pr_line(pr) for pr in p.prs)
    return (
        f"{names}{description} <sub>{_counts(p.prs)}</sub>\n"
        f"<details><summary>{summary}</summary>\n\n{lines}\n\n</details>"
    )


def _manual_line(m: ManualEntry) -> str:
    return f"**{m.name}** <sub>{m.label}</sub> — {_sentence(m.description)} <sub>{m.count}</sub>"


def render_body(projects: list[Project], manual: tuple[ManualEntry, ...]) -> str:
    blocks = [_project_block(p) for p in projects] + [_manual_line(m) for m in manual]
    return "\n\n".join(blocks)


def render_footer(updated: date) -> str:
    return f"<sub>Updated automatically · {updated:%b} {updated.day}, {updated.year}</sub>"
