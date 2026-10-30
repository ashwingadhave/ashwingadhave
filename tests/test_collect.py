import dataclasses
import unittest
from collections import Counter
from datetime import date

from profile_oss.collect import repo_from_api_url, repos_in, select_prs
from tests.helpers import fixture_repos, fixture_config, search_items


class SelectPrsTest(unittest.TestCase):
    def setUp(self):
        self.items = search_items()
        self.repos = fixture_repos()
        self.config = fixture_config()

    def select(self, config=None):
        return select_prs(self.items, self.repos, config or self.config)

    def test_select_keeps_merged_and_in_review(self):
        prs = self.select()
        self.assertEqual(
            dict(Counter(pr.repo for pr in prs)),
            {
                "truera/trulens": 2,
                "mlflow/mlflow": 1,
                "forcedotcom/sf-skills": 3,
                "jsforce/jsforce": 1,
            },
        )
        sf_statuses = sorted(pr.status for pr in prs if pr.repo == "forcedotcom/sf-skills")
        self.assertEqual(sf_statuses, ["in_review", "in_review", "merged"])

    def test_select_drops_drafts_closed_own_and_excluded(self):
        prs = self.select()
        self.assertNotIn(383, [pr.number for pr in prs if pr.repo == "forcedotcom/sf-skills"])
        self.assertNotIn(1, [pr.number for pr in prs if pr.repo == "forcedotcom/sf-skills"])
        repos = {pr.repo for pr in prs}
        for dropped in (
            "alvinreal/awesome-opensource-ai",
            "ashwingadhave/example-own-repo",
            "some/repo",
        ):
            self.assertNotIn(dropped, repos)

    def test_select_drops_missing_and_private_repos(self):
        repos = {pr.repo for pr in self.select()}
        self.assertNotIn("private-org/private-repo", repos)
        self.assertNotIn("gone/repo", repos)

    def test_select_honours_exclude_prs(self):
        config = dataclasses.replace(self.config, exclude_prs=frozenset({"truera/trulens#3007"}))
        trulens = [pr for pr in self.select(config) if pr.repo == "truera/trulens"]
        self.assertEqual([pr.number for pr in trulens], [2988])

    def test_when_uses_merge_date_for_merged(self):
        merged = [pr for pr in self.select() if pr.number == 3007][0]
        self.assertEqual(merged.status, "merged")
        self.assertEqual(merged.when, date(2026, 10, 28))
        in_review = [pr for pr in self.select() if pr.number == 2988][0]
        self.assertEqual(in_review.when, date(2026, 10, 23))

    def test_repo_from_api_url(self):
        self.assertEqual(
            repo_from_api_url("https://api.github.com/repos/truera/trulens"),
            "truera/trulens",
        )

    def test_repos_in_lists_each_repo_once(self):
        self.assertIn("truera/trulens", repos_in(self.items))
        self.assertEqual(len(repos_in(self.items)), 9)



class FixturePrivacyTest(unittest.TestCase):
    def test_fixture_uses_only_public_or_placeholder_repos(self):
        allowed = {
            "truera/trulens", "mlflow/mlflow", "forcedotcom/sf-skills", "jsforce/jsforce",
            "alvinreal/awesome-opensource-ai",
            "ashwingadhave/example-own-repo", "private-org/private-repo", "some/repo", "gone/repo",
        }
        self.assertLessEqual(repos_in(search_items()), allowed)


if __name__ == "__main__":
    unittest.main()
