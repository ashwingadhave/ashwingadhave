import unittest
from datetime import date

from profile_oss.readme import MarkerError, update_readme

START, END = "<!-- OSS:START -->", "<!-- OSS:END -->"
README = f"# A\n{START}\n{END}\n# B\n"
BODY = "**[TruLens](https://github.com/truera/trulens)** <sub>3.6k★</sub>"


class UpdateReadmeTest(unittest.TestCase):
    def test_update_readme_inserts_body_and_footer(self):
        text, changed = update_readme(README, BODY, date(2026, 10, 29))
        self.assertTrue(changed)
        self.assertIn(BODY, text)
        self.assertIn("Oct 29, 2026", text)
        self.assertTrue(text.startswith("# A\n" + START))
        self.assertTrue(text.endswith(END + "\n# B\n"))

    def test_update_readme_keeps_old_date_when_body_same(self):
        first, _ = update_readme(README, BODY, date(2026, 10, 29))
        second, changed = update_readme(first, BODY, date(2026, 11, 5))
        self.assertFalse(changed)
        self.assertEqual(second, first)
        self.assertIn("Oct 29, 2026", second)

    def test_update_readme_changes_date_when_body_changes(self):
        first, _ = update_readme(README, BODY, date(2026, 10, 29))
        second, changed = update_readme(first, BODY + " more", date(2026, 11, 5))
        self.assertTrue(changed)
        self.assertIn("Nov 5, 2026", second)
        self.assertNotIn("Oct 29, 2026", second)

    def test_update_readme_rejects_bad_markers(self):
        bad = [
            f"# A\n{END}\n",
            f"# A\n{START}\n",
            f"{START}\n{START}\n{END}\n",
            f"{END}\n{START}\n",
        ]
        for text in bad:
            with self.subTest(text=text):
                with self.assertRaises(MarkerError):
                    update_readme(text, BODY, date(2026, 10, 29))


if __name__ == "__main__":
    unittest.main()
