import csv
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from cadence.audio_features import AudioFeatures
from cadence.training import (
    _postprocess_model_labels,
    normalize_chord_label,
    read_annotations,
    read_split,
    train_and_evaluate,
)


class ChordLabelTests(unittest.TestCase):
    def test_normalizes_chart_extensions_inversions_and_enharmonic_roots(self) -> None:
        self.assertEqual(normalize_chord_label("Bb major"), "A#")
        self.assertEqual(normalize_chord_label("D# major 7"), "D#")
        self.assertEqual(normalize_chord_label("E7"), "E")
        self.assertEqual(normalize_chord_label("Gm/Bb"), "Gm")
        self.assertEqual(normalize_chord_label("Eaug"), "Eaug")
        self.assertEqual(normalize_chord_label("No chords (drums only)"), "N")

    def test_rejects_chord_qualities_outside_the_supported_vocabulary(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported chord quality"):
            normalize_chord_label("Csus4")


class TrainingInputTests(unittest.TestCase):
    def test_demo_two_intro_labels_match_the_chart_timing_clarification(self) -> None:
        root = Path(__file__).resolve().parents[1]
        annotations = read_annotations(
            root / "data" / "training" / "annotations.csv",
            root,
        )
        bar_nine_start = 1 + 8 * 4 * 60 / 148
        intro = [
            annotation
            for annotation in annotations
            if annotation.song_id == "demo_2"
            and annotation.start_seconds < bar_nine_start
        ]

        self.assertEqual(
            [
                (
                    annotation.start_seconds,
                    annotation.end_seconds,
                    annotation.chord_label,
                )
                for annotation in intro
            ],
            [
                (1.0, 1.405405, "G"),
                (1.405405, 7.486486, "N"),
                (7.486486, 7.891892, "G"),
                (7.891892, 13.972973, "N"),
            ],
        )

    def test_rejects_overlapping_annotations(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "annotations.csv"
            path.write_text(
                "song_id,audio_path,start_seconds,end_seconds,chord_label\n"
                "one,audio.mp3,0,1,C\n"
                "one,audio.mp3,0.5,2,G\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "Overlapping annotation"):
                read_annotations(path, root)

    def test_rejects_song_in_both_training_and_holdout(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "split.json"
            path.write_text(
                json.dumps(
                    {"training_song_ids": ["one"], "held_out_song_id": "one"}
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "both training and holdout"):
                read_split(path)


class TrainingEvaluationTests(unittest.TestCase):
    def test_model_postprocessing_smooths_short_runs_and_masks_silence(self) -> None:
        predictions = np.array(["C"] * 10 + ["G"] + ["C"] * 14, dtype="<U8")
        rms = np.ones(predictions.size, dtype=np.float32)
        rms[-1] = 0
        features = AudioFeatures(
            chroma=np.zeros((12, predictions.size), dtype=np.float32),
            rms=rms,
            sample_rate=22050,
            duration=0.6,
        )

        processed = _postprocess_model_labels(predictions, features)

        self.assertNotIn("G", processed)
        self.assertEqual(processed[-1], "N")

    def test_trains_and_scores_both_methods_on_the_same_held_out_frames(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            audio = root / "audio"
            audio.mkdir()
            for song_id in ("train_a", "train_b", "holdout"):
                (audio / f"{song_id}.mp3").touch()
            annotations_path = root / "annotations.csv"
            with annotations_path.open("w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(
                    file,
                    fieldnames=(
                        "song_id",
                        "audio_path",
                        "start_seconds",
                        "end_seconds",
                        "chord_label",
                    ),
                )
                writer.writeheader()
                for song_id, first_label, second_label in (
                    ("train_a", "C", "G"),
                    ("train_b", "C", "G"),
                    ("holdout", "C", "G"),
                ):
                    writer.writerow(
                        {
                            "song_id": song_id,
                            "audio_path": f"audio/{song_id}.mp3",
                            "start_seconds": 0,
                            "end_seconds": 0.05,
                            "chord_label": first_label,
                        }
                    )
                    writer.writerow(
                        {
                            "song_id": song_id,
                            "audio_path": f"audio/{song_id}.mp3",
                            "start_seconds": 0.05,
                            "end_seconds": 0.10,
                            "chord_label": second_label,
                        }
                    )
            split_path = root / "split.json"
            split_path.write_text(
                json.dumps(
                    {
                        "training_song_ids": ["train_a", "train_b"],
                        "held_out_song_id": "holdout",
                    }
                ),
                encoding="utf-8",
            )
            model_path = root / "models" / "model.joblib"

            chroma = np.zeros((12, 5), dtype=np.float32)
            chroma[[0, 4, 7], :2] = 1
            chroma[[7, 11, 2], 2:] = 1
            fake_features = AudioFeatures(
                chroma=chroma,
                rms=np.ones(5, dtype=np.float32),
                sample_rate=22050,
                duration=0.2,
            )

            report = train_and_evaluate(
                annotations_path,
                split_path,
                model_path,
                root=root,
                feature_loader=lambda _: fake_features,
            )

            self.assertEqual(report.model_metrics.frame_count, report.baseline_metrics.frame_count)
            self.assertEqual(report.model_metrics.frame_count, 5)
            self.assertTrue(model_path.is_file())
            self.assertEqual(report.split.held_out_song_id, "holdout")


if __name__ == "__main__":
    unittest.main()
