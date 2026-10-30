"""Regenerate the Open Source section of README.md.

Usage: python3 -m profile_oss [--dry-run]
Token: GITHUB_TOKEN, else GH_TOKEN.
"""

import argparse
import os
import sys
from datetime import date
from pathlib import Path

from profile_oss.collect import repos_in, select_prs
from profile_oss.config import load_config
from profile_oss.github import GitHubClient, GitHubError
from profile_oss.readme import MarkerError, update_readme
from profile_oss.render import build_projects, render_body, render_footer


def main(
    argv: list[str] | None = None,
    client: GitHubClient | None = None,
    root: Path = Path("."),
    today: date | None = None,
) -> int:
    parser = argparse.ArgumentParser(prog="profile_oss")
    parser.add_argument("--dry-run", action="store_true", help="print the section, write nothing")
    args = parser.parse_args(argv)
    today = today or date.today()

    if client is None:
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if not token:
            print("error: set GITHUB_TOKEN or GH_TOKEN", file=sys.stderr)
            return 2
        client = GitHubClient(token)

    config = load_config(root / "profile.toml")
    try:
        items = client.search_prs(config.owner)
        repos = {repo: client.repo_info(repo) for repo in sorted(repos_in(items))}
        prs = select_prs(items, repos, config)
        body = render_body(build_projects(prs, repos, config), config.manual)

        if args.dry_run:
            print(body + "\n\n" + render_footer(today))
            return 0

        readme_path = root / "README.md"
        text, changed = update_readme(readme_path.read_text(encoding="utf-8"), body, today)
    except (GitHubError, MarkerError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if changed:
        readme_path.write_text(text, encoding="utf-8")
    print("changed" if changed else "unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
