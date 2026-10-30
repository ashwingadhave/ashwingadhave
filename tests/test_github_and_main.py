import contextlib
import io
import shutil
import tempfile
import unittest
from datetime import date
from pathlib import Path

from profile_oss.__main__ import main
from profile_oss.github import GitHubClient, GitHubError
from tests.helpers import CONFIG_PATH, fixture_repos, search_items

README = "# Ashwin\n\n## 🧩 Open Source\n<!-- OSS:START -->\n<!-- OSS:END -->\n\n## Experience\n"


class FakeClient:
    def __init__(self, fail=False):
        self.fail = fail

    def search_prs(self, author):
        if self.fail:
            raise GitHubError("API rate limit exceeded")
        return search_items()

    def repo_info(self, full_name):
        return fixture_repos().get(full_name)


class GitHubClientTest(unittest.TestCase):
    def test_search_prs_paginates(self):
        calls = []

        def get_json(url):
            calls.append(url)
            if url.endswith("&page=1"):
                return 200, {"items": [{"n": i} for i in range(100)]}
            return 200, {"items": [{"n": i} for i in range(3)]}

        items = GitHubClient("t", get_json=get_json).search_prs("ashwingadhave")
        self.assertEqual(len(items), 103)
        self.assertEqual(len(calls), 2)
        self.assertIn("is%3Apublic", calls[0])
        self.assertIn("-user%3Aashwingadhave", calls[0])

    def test_repo_info_returns_none_on_404(self):
        client = GitHubClient("t", get_json=lambda url: (404, {"message": "Not Found"}))
        self.assertIsNone(client.repo_info("gone/repo"))

    def test_repo_info_maps_fields(self):
        payload = {
            "full_name": "truera/trulens",
            "html_url": "https://github.com/truera/trulens",
            "stargazers_count": 3620,
            "private": False,
            "description": "Evaluation and Tracking for LLM Experiments",
        }
        info = GitHubClient("t", get_json=lambda url: (200, payload)).repo_info("truera/trulens")
        self.assertEqual(info.stars, 3620)
        self.assertEqual(info.url, "https://github.com/truera/trulens")
        self.assertFalse(info.private)
        self.assertEqual(info.description, "Evaluation and Tracking for LLM Experiments")

    def test_repo_info_skips_blocked_repos(self):
        for status, body in ((451, {"message": "Repository access blocked"}),
                             (403, {"message": "Repository access blocked"})):
            client = GitHubClient("t", get_json=lambda url, r=(status, body): r)
            self.assertIsNone(client.repo_info("blocked/repo"))

    def test_other_errors_raise(self):
        client = GitHubClient("t", get_json=lambda url: (403, {"message": "rate limited"}))
        with self.assertRaises(GitHubError):
            client.repo_info("truera/trulens")


class MainTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        shutil.copy(CONFIG_PATH, self.tmp / "profile.toml")
        (self.tmp / "README.md").write_text(README, encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def run_main(self, argv, client):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(argv, client=client, root=self.tmp, today=date(2026, 10, 29))
        return code, out.getvalue(), err.getvalue()

    def readme(self):
        return (self.tmp / "README.md").read_text(encoding="utf-8")

    def test_main_writes_readme_and_reports_changed(self):
        code, out, _ = self.run_main([], FakeClient())
        self.assertEqual(code, 0)
        self.assertIn("changed", out)
        self.assertIn("**[MLflow](", self.readme())
        self.assertNotIn("private-org", self.readme())

    def test_main_dry_run_does_not_write(self):
        code, out, _ = self.run_main(["--dry-run"], FakeClient())
        self.assertEqual(code, 0)
        self.assertEqual(self.readme(), README)
        self.assertIn("Updated automatically", out)

    def test_main_leaves_readme_untouched_on_api_error(self):
        code, _, err = self.run_main([], FakeClient(fail=True))
        self.assertEqual(code, 1)
        self.assertEqual(self.readme(), README)
        self.assertIn("rate limit", err)

    def test_main_leaves_readme_untouched_on_marker_error(self):
        (self.tmp / "README.md").write_text("# no markers\n", encoding="utf-8")
        code, _, _ = self.run_main([], FakeClient())
        self.assertEqual(code, 1)
        self.assertEqual(self.readme(), "# no markers\n")


if __name__ == "__main__":
    unittest.main()
