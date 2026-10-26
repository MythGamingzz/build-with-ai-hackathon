import re
import unittest
from unittest.mock import Mock

from cadence.chord_model import ChordEvent
from cadence.chart_data import ChartBar, ChartChord, SectionRange, build_chart_data
from cadence.chart_pdf import _MeasureRow, create_chart_pdf
from cadence.progression_data import load_progressions


class ChartPdfTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.progressions = load_progressions()

    def _chart(self, bars: int):
        return build_chart_data(
            title="A practice chart",
            key="D major",
            tempo_bpm=120.0,
            time_signature="4/4",
            duration=bars * 2.0,
            events=(ChordEvent(0.0, 2.0, "D", 0.9),),
            sections=(SectionRange("Verse", 1, bars),),
            progressions=self.progressions,
        )

    def test_creates_a_pdf_with_expected_metadata_and_disclaimer(self) -> None:
        pdf_bytes = create_chart_pdf(self._chart(4))

        self.assertTrue(pdf_bytes.startswith(b"%PDF-"))
        self.assertIn(b"A practice chart", pdf_bytes)
        self.assertIn(b"D major", pdf_bytes)
        self.assertIn(b"experimental estimates", pdf_bytes)
        self.assertIn(b"Bar 1", pdf_bytes)
        self.assertIn(b"Bar 1 starts at the first predicted chord", pdf_bytes)
        self.assertNotIn(b"Beat 1", pdf_bytes)
        self.assertNotIn(b"1: D", pdf_bytes)

    def test_long_charts_flow_across_multiple_pages(self) -> None:
        pdf_bytes = create_chart_pdf(self._chart(100))
        page_count = len(re.findall(rb"/Type\s*/Page\b", pdf_bytes))

        self.assertGreater(page_count, 1)

    def test_corrected_labels_are_not_marked_in_the_printed_chart(self) -> None:
        chart = build_chart_data(
            title="Corrected chart",
            key="C major",
            tempo_bpm=120.0,
            time_signature="4/4",
            duration=2.0,
            events=(ChordEvent(0.0, 2.0, "G", 0.9),),
            sections=(SectionRange("Verse", 1, 1),),
            progressions=self.progressions,
            corrected_event_indices=frozenset({0}),
        )

        pdf_bytes = create_chart_pdf(chart)

        self.assertIn(b"G", pdf_bytes)
        self.assertNotIn(b"G*", pdf_bytes)
        self.assertNotIn(b"* marks a user-corrected chord label", pdf_bytes)

    def test_progression_matches_do_not_highlight_the_printed_chart(self) -> None:
        bar = ChartBar(
            1,
            (
                ChartChord(
                    beat=1.0,
                    label="C",
                    score=0.9,
                    highlighted=True,
                    event_index=0,
                ),
            ),
        )
        measure_row = _MeasureRow((bar,), beats_per_bar=4)
        measure_row.width = 100
        measure_row.canv = Mock()

        measure_row.draw()

        measure_row.canv.roundRect.assert_not_called()

    def test_progression_note_does_not_claim_the_pdf_has_highlights(self) -> None:
        progression = next(
            item
            for item in self.progressions
            if item.roman_numerals == ("I", "vi", "IV", "V")
        )
        chords = ("C", "Am", "F", "G")
        chart = build_chart_data(
            title="Progression chart",
            key="C major",
            tempo_bpm=120.0,
            time_signature="4/4",
            duration=8.0,
            events=tuple(
                ChordEvent(float(index * 2), float((index + 1) * 2), label, 0.9)
                for index, label in enumerate(chords)
            ),
            sections=(SectionRange("Verse", 1, 4),),
            progressions=(progression,),
        )

        pdf_bytes = create_chart_pdf(chart)

        self.assertIn(b"Possible progression", pdf_bytes)
        self.assertIn(b"verify against the audio", pdf_bytes)
        self.assertNotIn(b"highlighted chords", pdf_bytes)

    def test_fixed_chart_origin_is_explained_after_beat_edits(self) -> None:
        chart = build_chart_data(
            title="Moved chord",
            key="C major",
            tempo_bpm=120.0,
            time_signature="4/4",
            duration=4.0,
            events=(ChordEvent(2.0, 2.5, "E", 0.0),),
            sections=(SectionRange("Song", 1, 2),),
            progressions=self.progressions,
            corrected_event_indices=frozenset({0}),
            chart_start_seconds=0.0,
        )

        pdf_bytes = create_chart_pdf(chart)

        self.assertIn(
            b"Bar 1 stays anchored at the original chart start",
            pdf_bytes,
        )
        self.assertNotIn(b"Bar 1 starts at the first predicted chord", pdf_bytes)


if __name__ == "__main__":
    unittest.main()
