import tempfile
import unittest
from pathlib import Path

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression

from cadence.audio_features import AudioFeatures
from cadence.chord_model import (
    FEATURE_NAMES,
    ChordModelError,
    load_trained_model,
    predict_chord_events,
)


def _trained_model() -> LogisticRegression:
    c_major = np.zeros(12, dtype=np.float32)
    c_major[[0, 4, 7]] = 1
    g_major = np.zeros(12, dtype=np.float32)
    g_major[[7, 11, 2]] = 1
    return LogisticRegression(max_iter=1000).fit(
        np.stack([c_major] * 10 + [g_major] * 10),
        np.array(["C"] * 10 + ["G"] * 10),
    )


class TrainedModelTests(unittest.TestCase):
    def test_loads_only_a_compatible_saved_classifier(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "model.joblib"
            model = _trained_model()
            joblib.dump(
                {
                    "model": model,
                    "labels": tuple(str(label) for label in model.classes_),
                    "feature_names": FEATURE_NAMES,
                    "version": 1,
                },
                path,
            )

            loaded = load_trained_model(path)

            np.testing.assert_array_equal(loaded.classes_, model.classes_)

    def test_missing_model_has_an_actionable_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ChordModelError, "cadence.training"):
                load_trained_model(Path(directory) / "missing.joblib")

    def test_incompatible_saved_model_is_not_used(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "model.joblib"
            joblib.dump({"model": _trained_model(), "version": 0}, path)

            with self.assertRaisesRegex(ChordModelError, "incompatible"):
                load_trained_model(path)

    def test_corrupt_saved_model_has_an_actionable_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "model.joblib"
            path.write_bytes(b"not a model")

            with self.assertRaisesRegex(ChordModelError, "could not be loaded"):
                load_trained_model(path)

    def test_predictions_become_timed_chord_events(self) -> None:
        model = _trained_model()
        chroma = np.zeros((12, 80), dtype=np.float32)
        chroma[[0, 4, 7], :40] = 1
        chroma[[7, 11, 2], 40:] = 1
        frame_seconds = 512 / 22050
        features = AudioFeatures(
            chroma=chroma,
            rms=np.ones(80, dtype=np.float32),
            sample_rate=22050,
            duration=80 * frame_seconds,
        )

        events = predict_chord_events(features, model)

        self.assertEqual([event.label for event in events], ["C", "G"])
        self.assertAlmostEqual(events[0].start_seconds, 0)
        self.assertAlmostEqual(events[-1].end_seconds, features.duration)
        self.assertTrue(all(0 <= event.score <= 1 for event in events))


if __name__ == "__main__":
    unittest.main()
