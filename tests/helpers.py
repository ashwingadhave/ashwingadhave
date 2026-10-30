import json
from pathlib import Path

from profile_oss.collect import RepoInfo
from profile_oss.config import load_config

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = Path(__file__).resolve().parent / "fixtures"
CONFIG_PATH = FIXTURES / "profile.toml"  # a frozen copy, so edits to the live profile.toml never break tests


def search_items() -> list[dict]:
    return json.loads((FIXTURES / "search_items.json").read_text(encoding="utf-8"))


def fixture_config():
    return load_config(CONFIG_PATH)


def public(full_name: str, stars: int, description: str | None = None) -> RepoInfo:
    return RepoInfo(
        full_name=full_name,
        url=f"https://github.com/{full_name}",
        stars=stars,
        private=False,
        description=description,
    )


def fixture_repos() -> dict[str, RepoInfo | None]:
    return {
        "truera/trulens": public("truera/trulens", 3620),
        "mlflow/mlflow": public("mlflow/mlflow", 28590),
        "forcedotcom/sf-skills": public("forcedotcom/sf-skills", 1132),
        "jsforce/jsforce": public("jsforce/jsforce", 1474),
        "alvinreal/awesome-opensource-ai": public("alvinreal/awesome-opensource-ai", 900),
        "private-org/private-repo": RepoInfo(
            full_name="private-org/private-repo",
            url="https://github.com/private-org/private-repo",
            stars=0,
            private=True,
            description=None,
        ),
        "some/repo": public("some/repo", 10),
        "gone/repo": None,
    }
