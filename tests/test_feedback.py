import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from cadence.chord_model import ChordEvent
from cadence.feedback import (
    FeedbackSaveError,
    feedback_annotation_paths,
    save_feedback_example,
)
from cadence.training import read_annotations


class FeedbackSaveTests(unittest.TestCase):
    def test_saves_only_changed_intervals_and_can_update_the_example(self) -> None:
        original = (
            ChordEvent(0.0, 1.0, "C", 0.8),
            ChordEvent(1.0, 2.0, "G", 0.7),
        )
        corrected = (replace(original[0], label="D"), original[1])

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            feedback_id = save_feedback_example(
                audio_bytes=b"authorized-local-audio",
                filename="sample.wav",
                original_events=original,
                corrected_events=corrected,
                root=root,
            )
            manifest = (
                root / "output" / "training-feedback" / feedback_id / "annotations.csv"
            )
            annotations = read_annotations(manifest, root)

            self.assertEqual([item.chord_label for item in annotations], ["D"])
            self.assertEqual(annotations[0].song_id, feedback_id)
            self.assertEqual(
                annotations[0].audio_path.read_bytes(),
                b"authorized-local-audio",
            )
            self.assertEqual(feedback_annotation_paths(root), (manifest,))

            updated = (replace(original[0], label="D"), replace(original[1], label="N"))
            saved_again = save_feedback_example(
                audio_bytes=b"authorized-local-audio",
                filename="sample.wav",
                original_events=original,
                corrected_events=updated,
                root=root,
                feedback_id=feedback_id,
            )

            self.assertEqual(saved_again, feedback_id)
            self.assertEqual(
                [item.chord_label for item in read_annotations(manifest, root)],
                ["D", "N"],
            )

    def test_rejects_missing_changes_and_changed_event_timing(self) -> None:
        original = (ChordEvent(0.0, 1.0, "C", 0.8),)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaisesRegex(FeedbackSaveError, "Change at least one"):
                save_feedback_example(
                    audio_bytes=b"audio",
                    filename="sample.wav",
                    original_events=original,
                    corrected_events=original,
                    root=root,
                )
            with self.assertRaisesRegex(FeedbackSaveError, "timing or score"):
                save_feedback_example(
                    audio_bytes=b"audio",
                    filename="sample.wav",
                    original_events=original,
                    corrected_events=(ChordEvent(0.0, 2.0, "D", 0.8),),
                    root=root,
                )

    def test_rejects_unsupported_audio_and_feedback_identifiers(self) -> None:
        original = (ChordEvent(0.0, 1.0, "C", 0.8),)
        corrected = (replace(original[0], label="D"),)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaisesRegex(FeedbackSaveError, "WAV and MP3"):
                save_feedback_example(
                    audio_bytes=b"audio",
                    filename="sample.flac",
                    original_events=original,
                    corrected_events=corrected,
                    root=root,
                )
            with self.assertRaisesRegex(FeedbackSaveError, "identifier"):
                save_feedback_example(
                    audio_bytes=b"audio",
                    filename="sample.wav",
                    original_events=original,
                    corrected_events=corrected,
                    root=root,
                    feedback_id="../escape",
                )

    def test_saves_corrected_beat_cell_boundaries(self) -> None:
        original = (
            ChordEvent(1.5, 2.0, ".", 0.0),
            ChordEvent(2.0, 2.5, ".", 0.0),
        )
        corrected = (
            ChordEvent(1.5, 2.0, "N", 0.0),
            ChordEvent(2.0, 2.5, "E", 0.0),
        )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            feedback_id = save_feedback_example(
                audio_bytes=b"authorized-local-audio",
                filename="sample.wav",
                original_events=original,
                corrected_events=corrected,
                root=root,
            )
            annotations = read_annotations(
                root
                / "output"
                / "training-feedback"
                / feedback_id
                / "annotations.csv",
                root,
            )

        self.assertEqual(
            [
                (item.start_seconds, item.end_seconds, item.chord_label)
                for item in annotations
            ],
            [(1.5, 2.0, "N"), (2.0, 2.5, "E")],
        )


if __name__ == "__main__":
    unittest.main()
