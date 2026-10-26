import unittest
from dataclasses import replace

from app import _beat_cell_default, _matched_chord_html
from cadence.chart_data import ChartChord
from cadence.progression_data import load_progressions


class ChartUiTests(unittest.TestCase):
    def test_beat_editor_defaults_empty_and_no_chord_cells(self) -> None:
        self.assertEqual(_beat_cell_default(()), ".")
        self.assertEqual(
            _beat_cell_default(
                (
                    ChartChord(
                        beat=1.0,
                        label="N",
                        score=0.0,
                        highlighted=False,
                        event_index=0,
                    ),
                )
            ),
            "N",
        )

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
        self.assertIn(
            '<a class="chart-match-link" href="?lesson=I-vi-IV-V"',
            markup,
        )
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

    def test_direct_match_link_marks_a_user_corrected_chord(self) -> None:
        progression = next(
            item
            for item in load_progressions()
            if item.id == "I-vi-IV-V"
        )

        markup = _matched_chord_html(
            "B",
            progression,
            "D",
            is_user_corrected=True,
        )

        self.assertIn('class="chart-match">B*</span>', markup)
        self.assertIn("User-corrected chord.", markup)


if __name__ == "__main__":
    unittest.main()
