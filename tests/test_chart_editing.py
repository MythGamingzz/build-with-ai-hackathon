import unittest

from cadence.chord_model import ChordEvent
from cadence.chart_data import SectionRange, build_chart_data, bar_beat_slots
from cadence.chart_editing import (
    BeatCellEditError,
    apply_beat_cell_edits,
    default_beat_cells,
    parse_beat_cell,
)
from cadence.progression_data import load_progressions


class BeatCellEditTests(unittest.TestCase):
    def test_accepts_chord_symbols_and_both_no_chord_markers(self) -> None:
        self.assertEqual(parse_beat_cell(" E "), ("E",))
        self.assertEqual(parse_beat_cell("N"), ("N",))
        self.assertEqual(parse_beat_cell("."), ("N",))

    def test_rejects_empty_and_unsupported_cells(self) -> None:
        for value in ("", "H", "C/G", "N / C", "C, G"):
            with self.subTest(value=value):
                with self.assertRaises(BeatCellEditError):
                    parse_beat_cell(value)

    def test_moves_chord_to_next_bar_beat_one_and_keeps_chart_anchor(self) -> None:
        events = (
            ChordEvent(0.0, 1.7, "B", 0.8),
            ChordEvent(1.7, 4.0, "E", 0.7),
        )
        defaults = default_beat_cells(
            events,
            duration=4.0,
            tempo_bpm=120.0,
            time_signature="4/4",
        )
        self.assertEqual(defaults[(1, 4)], "E")
        self.assertEqual(defaults[(2, 1)], ".")

        values = dict(defaults)
        values[(1, 4)] = "."
        values[(2, 1)] = "E"
        edited = apply_beat_cell_edits(
            events,
            values,
            duration=4.0,
            tempo_bpm=120.0,
            time_signature="4/4",
        )
        chart = build_chart_data(
            title="Bar boundary check",
            key="B major",
            tempo_bpm=120.0,
            time_signature="4/4",
            duration=4.0,
            events=edited.events,
            sections=(SectionRange("Song", 1, 2),),
            progressions=load_progressions(),
            corrected_event_indices=edited.corrected_event_indices,
            chart_start_seconds=edited.chart_start_seconds,
        )

        self.assertEqual(edited.chart_start_seconds, 0.0)
        self.assertTrue(chart.chart_start_is_fixed)
        self.assertEqual(
            [
                chord.label
                for chord in bar_beat_slots(
                    chart.groups[0].bars[0],
                    4,
                    include_no_chord=True,
                )[3]
            ],
            ["N"],
        )
        self.assertEqual(
            [
                chord.label
                for chord in bar_beat_slots(chart.groups[0].bars[1], 4)[0]
            ],
            ["E"],
        )
        self.assertEqual(
            [event.start_seconds for event in edited.corrected_feedback_events],
            [1.5, 2.0],
        )
        self.assertEqual(
            [event.label for event in edited.corrected_feedback_events],
            ["N", "E"],
        )
        self.assertEqual(
            edited.corrected_event_indices,
            frozenset(
                chord.event_index
                for group in chart.groups
                for bar in group.bars
                for chord in bar.chords
                if chord.is_user_corrected
            ),
        )

    def test_keeps_unchanged_multiple_predictions_without_rewriting_them(self) -> None:
        events = (
            ChordEvent(0.0, 0.5, "C", 0.8),
            ChordEvent(0.2, 0.5, "G", 0.7),
        )
        values = default_beat_cells(
            events,
            duration=2.0,
            tempo_bpm=120.0,
            time_signature="4/4",
        )
        edited = apply_beat_cell_edits(
            events,
            values,
            duration=2.0,
            tempo_bpm=120.0,
            time_signature="4/4",
        )

        self.assertEqual(edited.events, events)
        self.assertEqual(edited.changed_cell_count, 0)
        self.assertEqual(edited.corrected_event_indices, frozenset())


if __name__ == "__main__":
    unittest.main()
