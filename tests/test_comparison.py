import json
from pathlib import Path
import tempfile
import unittest

from cadence.comparison import (
    Annotation,
    Reference,
    build_report_html,
    compare_annotations,
    load_reference,
)


class ReferenceLoadingTests(unittest.TestCase):
    def write_reference(self, path: Path, content: dict[str, object]) -> None:
        path.write_text(json.dumps(content), encoding="utf-8")

    def test_loads_timed_reference_annotations(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "reference.json"
            self.write_reference(
                path,
                {
                    "recording": "sample.wav",
                    "lyrics": [{"start": 0.5, "end": 1.0, "text": "hello"}],
                    "chords": [{"start": 0.0, "end": 0.5, "label": "G"}],
                },
            )

            reference = load_reference(path, "sample.wav", 2.0)

        self.assertEqual(reference.lyrics[0].label, "hello")
        self.assertEqual(reference.chords[0].label, "G")

    def test_rejects_a_reference_for_a_different_recording(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "reference.json"
            self.write_reference(path, {"recording": "other.wav", "lyrics": [], "chords": []})

            with self.assertRaisesRegex(ValueError, "must be named"):
                load_reference(path, "sample.wav", 2.0)

    def test_rejects_annotations_outside_recording_duration(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "reference.json"
            self.write_reference(
                path,
                {
                    "recording": "sample.wav",
                    "lyrics": [],
                    "chords": [{"start": 1.5, "end": 2.5, "label": "G"}],
                },
            )

            with self.assertRaisesRegex(ValueError, "fit within"):
                load_reference(path, "sample.wav", 2.0)


class AnnotationComparisonTests(unittest.TestCase):
    def setUp(self) -> None:
        self.reference = Reference(
            recording="sample.wav",
            lyrics=[],
            chords=[
                Annotation(0.0, 1.0, "G"),
                Annotation(1.0, 2.0, "E"),
            ],
        )

    def test_counts_matching_and_mismatching_chord_spans(self) -> None:
        result = compare_annotations(
            {
                "chords": [
                    {"start": 0.0, "end": 1.0, "label": "G"},
                    {"start": 1.0, "end": 2.0, "label": "C#m"},
                ]
            },
            self.reference,
        )

        self.assertEqual(
            [row["status"] for row in result["rows"]], ["Match", "Mismatch"]
        )
        self.assertEqual(result["summary"]["chords"]["matched"], 1)

    def test_report_escapes_annotation_text_and_labels_sources(self) -> None:
        reference = Reference(
            recording="sample.wav",
            lyrics=[
                Annotation(0.0, 1.0, "<script>alert(1)</script>")
            ],
            chords=[],
        )
        analysis = {
            "duration_seconds": 1.0,
            "lyrics": [
                {"start": 0.0, "end": 1.0, "text": "<script>alert(1)</script>"}
            ],
            "chords": [],
        }
        comparison = compare_annotations(analysis, reference)

        html = build_report_html(analysis, reference, comparison)

        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn("<script>", html)
        self.assertIn("Estimate", html)
        self.assertIn("Reference", html)


if __name__ == "__main__":
    unittest.main()
