import unittest

from cadence.chord_model import ChordEvent
from cadence.chart_data import (
    ChartData,
    ChartDataError,
    SectionRange,
    build_chart_data,
    bar_beat_slots,
    format_bar_measure,
)
from cadence.progression_data import load_progressions
from cadence.theory import spell_progression


class ChartDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.progressions = load_progressions()
        cls.target = next(
            progression
            for progression in cls.progressions
            if progression.roman_numerals == ("I", "vi", "IV", "V")
        )

    def _events(self, labels: list[str]) -> tuple[ChordEvent, ...]:
        return tuple(
            ChordEvent(
                start_seconds=index * 2.0,
                end_seconds=(index + 1) * 2.0,
                label=label,
                score=0.8,
            )
            for index, label in enumerate(labels)
        )

    def _build(
        self,
        *,
        duration: float = 10.0,
        events: tuple[ChordEvent, ...] = (),
        sections: tuple[SectionRange, ...] = (),
        title: str = "Practice song",
    ) -> ChartData:
        return build_chart_data(
            title=title,
            key="C major",
            tempo_bpm=120.0,
            time_signature="4/4",
            duration=duration,
            events=events,
            sections=sections,
            progressions=self.progressions,
        )

    def test_groups_named_sections_and_unsectioned_bars(self) -> None:
        chart = self._build(
            duration=12.0,
            sections=(
                SectionRange("Verse", 1, 2),
                SectionRange("Chorus", 4, 5),
            ),
        )

        self.assertEqual(
            [(group.name, [bar.number for bar in group.bars]) for group in chart.groups],
            [
                ("Verse", [1, 2]),
                ("Chorus", [4, 5]),
                ("Unsectioned", [3, 6]),
            ],
        )

    def test_unique_section_match_highlights_its_chord_events(self) -> None:
        chords = spell_progression(
            self.target.degrees,
            "C",
            self.target.qualities,
        )
        events = self._events([chord.symbol for chord in chords])

        chart = self._build(
            events=events,
            sections=(SectionRange("Verse", 1, 4),),
        )

        verse = chart.groups[0]
        self.assertIs(verse.match.progression, self.target)
        self.assertEqual(
            [
                chord.label
                for bar in verse.bars
                for chord in bar.chords
                if chord.highlighted
            ],
            [chord.symbol for chord in chords],
        )
        self.assertEqual([bar.number for bar in chart.groups[1].bars], [5])

    def test_progression_cannot_match_across_confirmed_sections(self) -> None:
        chords = spell_progression(
            self.target.degrees,
            "C",
            self.target.qualities,
        )
        chart = self._build(
            events=self._events([chord.symbol for chord in chords]),
            duration=8.0,
            sections=(
                SectionRange("Verse", 1, 2),
                SectionRange("Chorus", 3, 4),
            ),
        )

        self.assertTrue(
            all(
                group.match is None or group.match.progression is not self.target
                for group in chart.groups
            )
        )

    def test_unnamed_section_is_included_in_unsectioned_group(self) -> None:
        chart = self._build(
            duration=8.0,
            sections=(SectionRange("", 1, 2),),
        )

        self.assertEqual([group.name for group in chart.groups], ["Unsectioned"])
        self.assertEqual([bar.number for bar in chart.groups[0].bars], [1, 2, 3, 4])

    def test_measure_format_shows_chords_and_dots_without_beat_numbers(self) -> None:
        chart = self._build(
            duration=6.0,
            events=(
                ChordEvent(0.0, 1.0, "N", 0.8),
                ChordEvent(1.0, 2.0, "B", 0.8),
                ChordEvent(2.0, 3.0, "D#m", 0.8),
            ),
            sections=(SectionRange("Verse", 1, 3),),
        )

        measure = format_bar_measure(chart.groups[0].bars[0], 4)

        self.assertEqual(measure, "| B . D#m . |")
        self.assertEqual(chart.chart_start_seconds, 1.0)
        self.assertEqual(chart.duration, 5.0)
        self.assertNotIn("1:", measure)
        self.assertNotIn("3:", measure)
        self.assertNotIn("N", measure)

    def test_all_no_chord_events_keep_full_duration_and_render_as_dots(self) -> None:
        chart = self._build(
            duration=4.0,
            events=(ChordEvent(0.0, 4.0, "N", 0.9),),
            sections=(SectionRange("Song", 1, 2),),
        )

        self.assertIsNone(chart.chart_start_seconds)
        self.assertEqual(chart.duration, 4.0)
        self.assertEqual(
            format_bar_measure(chart.groups[0].bars[0], 4),
            "| . . . . |",
        )

    def test_chart_cells_keep_event_indices_for_direct_chord_editing(self) -> None:
        chart = self._build(
            duration=8.0,
            events=(
                ChordEvent(0.0, 1.0, "C", 0.8),
                ChordEvent(1.0, 2.0, "N", 0.0),
                ChordEvent(2.0, 3.0, "G", 0.7),
            ),
            sections=(SectionRange("Verse", 1, 4),),
        )
        bar = chart.groups[0].bars[0]

        visible_slots = bar_beat_slots(bar, 4)
        editable_slots = bar_beat_slots(bar, 4, include_no_chord=True)

        self.assertEqual(visible_slots[0][0].event_index, 0)
        self.assertEqual(visible_slots[2], ())
        self.assertEqual(editable_slots[2][0].event_index, 1)
        self.assertEqual(editable_slots[2][0].label, "N")
        self.assertEqual(chart.groups[0].bars[1].chords[0].event_index, 2)

    def test_corrected_event_indices_are_retained_in_chart_data(self) -> None:
        chart = build_chart_data(
            title="Practice song",
            key="C major",
            tempo_bpm=120.0,
            time_signature="4/4",
            duration=4.0,
            events=self._events(["C", "G"]),
            sections=(SectionRange("Verse", 1, 2),),
            progressions=self.progressions,
            corrected_event_indices=frozenset({1}),
        )

        chords = [
            chord
            for bar in chart.groups[0].bars
            for chord in bar.chords
        ]

        self.assertEqual([chord.is_user_corrected for chord in chords], [False, True])

    def test_rejects_overlapping_section_ranges(self) -> None:
        with self.assertRaisesRegex(ChartDataError, "overlaps"):
            self._build(
                duration=8.0,
                sections=(
                    SectionRange("Verse", 1, 3),
                    SectionRange("Chorus", 3, 4),
                ),
            )

    def test_rejects_section_ranges_outside_the_chart(self) -> None:
        with self.assertRaisesRegex(ChartDataError, "bar numbers"):
            self._build(
                duration=8.0,
                sections=(SectionRange("Outro", 5, 5),),
            )

    def test_rejects_missing_title_and_invalid_chord_timing(self) -> None:
        with self.assertRaisesRegex(ChartDataError, "song title"):
            self._build(title="  ")
        invalid_event = ChordEvent(2.0, 1.0, "C", 0.8)
        with self.assertRaisesRegex(ChartDataError, "invalid timing"):
            self._build(events=(invalid_event,))


if __name__ == "__main__":
    unittest.main()
