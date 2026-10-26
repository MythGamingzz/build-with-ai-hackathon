import unittest
from dataclasses import replace

from app import _matched_chord_html
from cadence.progression_data import load_progressions


class ChartUiTests(unittest.TestCase):
    def test_match_tooltip_includes_progression_details_and_clickable_lesson(self) -> None:
        progression = next(
            item
            for item in load_progressions()
            if item.id == "I-vi-IV-V"
        )

        markup = _matched_chord_html("B", progression, "D")

        self.assertIn('class="chart-hover-match"', markup)
        self.assertIn("The familiar four-chord loop", markup)
        self.assertIn("(I-vi-IV-V) in D", markup)
        self.assertIn('href="?lesson=I-vi-IV-V"', markup)
        self.assertIn("Open progression lesson", markup)

    def test_match_tooltip_escapes_progression_text(self) -> None:
        progression = replace(
            next(iter(load_progressions())),
            name='<script>alert("x")</script>',
        )

        markup = _matched_chord_html("C", progression, "C")

        self.assertNotIn("<script>", markup)
        self.assertIn("&lt;script&gt;", markup)


if __name__ == "__main__":
    unittest.main()
