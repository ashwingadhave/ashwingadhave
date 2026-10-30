import tempfile
import unittest
from pathlib import Path

from profile_oss.config import load_config

ROOT = Path(__file__).resolve().parent.parent


class LoadConfigTest(unittest.TestCase):
    def test_load_config_reads_fixture_profile_toml(self):
        from tests.helpers import CONFIG_PATH

        config = load_config(CONFIG_PATH)
        self.assertEqual(config.owner, "ashwingadhave")
        self.assertIn("alvinreal/awesome-opensource-ai", config.exclude_repos)
        self.assertEqual(config.exclude_prs, frozenset())
        self.assertEqual(len(config.projects), 3)
        self.assertEqual(
            tuple(ref.repo for ref in config.projects[2].repos),
            ("forcedotcom/sf-skills", "jsforce/jsforce"),
        )
        self.assertEqual(config.projects[1].repos[0].name, "TruLens")
        self.assertEqual(config.manual[0].count, "8 merged")

    def test_load_config_defaults_optional_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "profile.toml"
            path.write_text('owner = "x"\n', encoding="utf-8")
            config = load_config(path)
        self.assertEqual(config.owner, "x")
        self.assertEqual(config.projects, ())
        self.assertEqual(config.manual, ())
        self.assertEqual(config.exclude_repos, frozenset())
        self.assertEqual(config.exclude_prs, frozenset())

    def test_tests_use_fixture_config_not_live_file(self):
        from tests import helpers

        self.assertEqual(helpers.CONFIG_PATH, helpers.FIXTURES / "profile.toml")

    def test_live_profile_toml_loads(self):
        self.assertTrue(load_config(ROOT / "profile.toml").owner)


if __name__ == "__main__":
    unittest.main()
