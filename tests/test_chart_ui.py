import unittest
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import patch

from app import (
    _beat_cell_default,
    _matched_chord_html,
    _progression_color_map,
    _undo_chart_edits,
)
from cadence.chart_data import ChartChord
from cadence.matching import ProgressionCandidate
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
        candidate = ProgressionCandidate(progression, "D", (0,))

        markup = _matched_chord_html(
            "B",
            (candidate,),
            _progression_color_map(load_progressions()),
            link_progression=progression,
        )

        self.assertIn('class="chart-hover-match"', markup)
        self.assertIn("The familiar four-chord loop", markup)
        self.assertIn("(I-vi-IV-V) in D", markup)
        self.assertIn(
            '<a class="chart-match-link" href="?lesson=I-vi-IV-V"',
            markup,
        )
        self.assertIn(
            '<a href="?lesson=I-vi-IV-V">Open progression lesson</a>',
            markup,
        )
        self.assertGreater(
            markup.index('<a href="?lesson=I-vi-IV-V">Open progression lesson</a>'),
            markup.index("(I-vi-IV-V) in D"),
        )

    def test_match_tooltip_escapes_progression_text(self) -> None:
        progression = replace(
            next(iter(load_progressions())),
            name='<script>alert("x")</script>',
        )
        candidate = ProgressionCandidate(progression, "C", (0,))

        markup = _matched_chord_html(
            "C",
            (candidate,),
            _progression_color_map((progression,)),
            link_progression=progression,
        )

        self.assertNotIn("<script>", markup)
        self.assertIn("&lt;script&gt;", markup)

    def test_direct_match_link_does_not_add_an_asterisk_for_corrected_chords(self) -> None:
        progression = next(
            item
            for item in load_progressions()
            if item.id == "I-vi-IV-V"
        )
        candidate = ProgressionCandidate(progression, "D", (0,))

        markup = _matched_chord_html(
            "B",
            (candidate,),
            _progression_color_map(load_progressions()),
            link_progression=progression,
        )

        self.assertIn(
            'class="chart-match" style="background: #f4c56a;">B</span>',
            markup,
        )
        self.assertNotIn("B*", markup)
        self.assertNotIn("User-corrected chord.", markup)

    def test_shared_match_blends_colors_and_links_each_candidate(self) -> None:
        progressions = load_progressions()
        candidates = tuple(
            ProgressionCandidate(
                progression=progression,
                key=key,
                matched_event_indices=(0,),
            )
            for progression, key in zip(progressions[:2], ("C", "D"), strict=True)
        )

        markup = _matched_chord_html(
            "C",
            candidates,
            _progression_color_map(progressions),
        )

        self.assertEqual(
            len(set(_progression_color_map(progressions).values())),
            len(progressions),
        )
        self.assertIn("linear-gradient(90deg", markup)
        self.assertIn("Possible progressions", markup)
        self.assertIn(candidates[0].progression.name, markup)
        self.assertIn(candidates[1].progression.name, markup)
        self.assertIn(" in C", markup)
        self.assertIn(" in D", markup)
        self.assertNotIn('class="chart-match-link"', markup)
        self.assertEqual(
            markup.count(">Open progression lesson</a>"),
            len(candidates),
        )
        for candidate in candidates:
            link = (
                f'<a href="?lesson={candidate.progression.id}">'
                "Open progression lesson</a>"
            )
            details = (
                f"{candidate.progression.name} "
                f"({candidate.progression.pattern}) in {candidate.key}"
            )
            self.assertIn(link, markup)
            self.assertGreater(markup.index(link), markup.index(details))

    def test_undo_restores_original_beat_values_and_clears_feedback(self) -> None:
        state = SimpleNamespace(
            analysis_beat_cell_values={(5, 4): ".", (6, 1): "E"},
            analysis_edit_mode=True,
            analysis_chart_undo_available=True,
            analysis_feedback_original_events=("original",),
            analysis_feedback_corrected_events=("corrected",),
            analysis_feedback_rights_confirmed=True,
            analysis_scroll_to_feedback=True,
        )
        with (
            patch("app.st.session_state", state),
            patch("app._update_chart_preview", return_value=True) as update_preview,
        ):
            self.assertTrue(_undo_chart_edits(None, ()))

        update_preview.assert_called_once_with(None, ())
        self.assertEqual(state.analysis_beat_cell_values, {})
        self.assertFalse(state.analysis_edit_mode)
        self.assertFalse(state.analysis_chart_undo_available)
        self.assertEqual(state.analysis_feedback_original_events, ())
        self.assertEqual(state.analysis_feedback_corrected_events, ())
        self.assertFalse(state.analysis_feedback_rights_confirmed)
        self.assertFalse(state.analysis_scroll_to_feedback)

    def test_failed_undo_preserves_beat_cell_values(self) -> None:
        values = {(5, 4): ".", (6, 1): "E"}
        state = SimpleNamespace(analysis_beat_cell_values=values)
        with (
            patch("app.st.session_state", state),
            patch("app._update_chart_preview", return_value=False),
        ):
            self.assertFalse(_undo_chart_edits(None, ()))

        self.assertEqual(state.analysis_beat_cell_values, values)


if __name__ == "__main__":
    unittest.main()
