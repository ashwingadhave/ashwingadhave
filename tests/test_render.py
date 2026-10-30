import unittest
from datetime import date

from profile_oss.collect import PR, select_prs
from profile_oss.render import (
    build_projects,
    clean_title,
    format_stars,
    render_body,
    render_footer,
)
from tests.helpers import fixture_repos, public, fixture_config, search_items

TRULENS_BLOCK = """\
**[TruLens](https://github.com/truera/trulens)** <sub>3.6k★</sub> — LLM eval metrics; test-suite reliability. <sub>1 merged · 1 in review</sub>
<details><summary>2 pull requests</summary>

- [repair broken notebook symlinks and guard against new ones](https://github.com/truera/trulens/pull/3007) — merged Oct 2026
- [add escalation correctness metric](https://github.com/truera/trulens/pull/2988) — in review

</details>"""

IMMIGRATION_VOICE_LINE = (
    "**ImmigrationVoice** <sub>nonprofit · volunteer</sub> — "
    "Congress API integration and legislator data model. <sub>8 merged</sub>"
)


def names(project):
    return " · ".join(name for name, _url, _stars in project.links)


class RenderTest(unittest.TestCase):
    def setUp(self):
        self.config = fixture_config()
        self.repos = fixture_repos()
        self.prs = select_prs(search_items(), self.repos, self.config)
        self.projects = build_projects(self.prs, self.repos, self.config)

    def test_format_stars(self):
        self.assertEqual(format_stars(950), "950★")
        self.assertEqual(format_stars(3620), "3.6k★")
        self.assertEqual(format_stars(28590), "28.6k★")
        self.assertEqual(format_stars(2000), "2k★")

    def test_clean_title(self):
        self.assertEqual(clean_title("fix(tests): repair x"), "repair x")
        self.assertEqual(clean_title("feat!: y"), "y")
        self.assertEqual(clean_title("Add a consistency example"), "Add a consistency example")

    def test_clean_title_keeps_non_commit_prefixes_and_never_empties(self):
        self.assertEqual(clean_title("MLflow: add tracing docs"), "MLflow: add tracing docs")
        self.assertEqual(clean_title("docs(eval): add example"), "add example")
        self.assertEqual(clean_title("fix: "), "fix: ")

    def test_build_projects_orders_by_stars_and_groups_repos(self):
        self.assertEqual(
            [names(p) for p in self.projects],
            ["MLflow", "TruLens", "Salesforce sf-skills · jsforce"],
        )
        self.assertEqual(self.projects[2].top_stars, 1474)

    def test_unknown_repo_gets_default_line(self):
        pr = PR(
            repo="motdotla/dotenv",
            number=1070,
            title="fix: something",
            url="https://github.com/motdotla/dotenv/pull/1070",
            status="merged",
            when=date(2026, 10, 1),
        )
        repos = {"motdotla/dotenv": public("motdotla/dotenv", 20000, "Loads env vars. Zero deps.")}
        [project] = build_projects([pr], repos, self.config)
        self.assertEqual(names(project), "dotenv")
        self.assertEqual(project.description, "Loads env vars.")

        repos = {"motdotla/dotenv": public("motdotla/dotenv", 20000, None)}
        body = render_body(build_projects([pr], repos, self.config), ())
        self.assertNotIn(" — ", body.splitlines()[0])

    def test_untrusted_repo_description_is_escaped(self):
        pr = PR(
            repo="evil/repo",
            number=1,
            title="fix: something",
            url="https://github.com/evil/repo/pull/1",
            status="merged",
            when=date(2026, 10, 1),
        )
        hostile = "<!-- OSS:END --> <img src=x> </details> [click](https://evil.example)"
        repos = {"evil/repo": public("evil/repo", 5, hostile)}
        body = render_body(build_projects([pr], repos, self.config), ())
        for raw in ("<!--", "<img", "</details> [", "[click]"):
            self.assertNotIn(raw, body.splitlines()[0])

    def test_render_body_matches_expected_block(self):
        body = render_body(self.projects, ())
        self.assertIn(TRULENS_BLOCK, body)

    def test_render_counts_and_singular_summary(self):
        body = render_body(self.projects, ())
        mlflow_block = body.split("\n\n**")[0]
        self.assertIn("<sub>1 in review</sub>", mlflow_block)
        self.assertIn("<summary>1 pull request</summary>", mlflow_block)

    def test_render_escapes_markdown_in_titles(self):
        pr = PR(
            repo="truera/trulens",
            number=1,
            title="fix: handle [x] <y> | z",
            url="https://github.com/truera/trulens/pull/1",
            status="in_review",
            when=date(2026, 10, 1),
        )
        body = render_body(build_projects([pr], self.repos, self.config), ())
        self.assertIn(r"[handle \[x\] &lt;y&gt; \| z](https://github.com/truera/trulens/pull/1)", body)

    def test_manual_entries_come_last(self):
        body = render_body(self.projects, self.config.manual)
        self.assertTrue(body.endswith(IMMIGRATION_VOICE_LINE))

    def test_render_footer(self):
        self.assertEqual(
            render_footer(date(2026, 10, 29)),
            "<sub>Updated automatically · Oct 29, 2026</sub>",
        )


if __name__ == "__main__":
    unittest.main()
