"""Replace the generated section between the OSS markers in README.md."""

from datetime import date

from profile_oss.render import render_footer

START = "<!-- OSS:START -->"
END = "<!-- OSS:END -->"
_FOOTER_PREFIX = "<sub>Updated automatically"


class MarkerError(ValueError):
    pass


def _strip_footer(section: str) -> str:
    lines = [line for line in section.strip().splitlines() if not line.startswith(_FOOTER_PREFIX)]
    return "\n".join(lines).strip()


def update_readme(text: str, body: str, today: date) -> tuple[str, bool]:
    if text.count(START) != 1 or text.count(END) != 1:
        raise MarkerError(f"README must contain {START} and {END} exactly once each")
    start = text.index(START) + len(START)
    end = text.index(END)
    if end < start:
        raise MarkerError(f"{END} comes before {START}")
    if _strip_footer(text[start:end]) == body.strip():
        return text, False
    section = "\n" + body + "\n\n" + render_footer(today) + "\n"
    return text[:start] + section + text[end:], True
