import re
import unittest

from cadence.chord_model import ChordEvent
from cadence.chart_data import SectionRange, build_chart_data
from cadence.chart_pdf import create_chart_pdf
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
        self.assertNotIn(b"Beat 1", pdf_bytes)
        self.assertNotIn(b"1: D", pdf_bytes)

    def test_long_charts_flow_across_multiple_pages(self) -> None:
        pdf_bytes = create_chart_pdf(self._chart(100))
        page_count = len(re.findall(rb"/Type\s*/Page\b", pdf_bytes))

        self.assertGreater(page_count, 1)


if __name__ == "__main__":
    unittest.main()
