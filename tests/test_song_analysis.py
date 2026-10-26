import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from cadence.audio_features import AudioFeatures
from cadence.chord_model import ChordEvent
from cadence.song_analysis import AudioAnalysisError, analyze_audio_bytes
from cadence.song_metadata import SongMetadataEstimate


class UploadedAudioTests(unittest.TestCase):
    def setUp(self) -> None:
        self.features = AudioFeatures(
            chroma=np.ones((12, 2), dtype=np.float32),
            rms=np.ones(2, dtype=np.float32),
            sample_rate=22050,
            duration=1.0,
        )
        self.metadata = SongMetadataEstimate(
            key="C major",
            key_strength=0.1,
            tempo_bpm=120,
            tempo_strength=0.2,
            time_signature="4/4",
            meter_strength=0.0,
            beat_times=(0.0, 0.5),
        )

    def test_rejects_non_audio_extensions_before_loading_the_model(self) -> None:
        with patch("cadence.song_analysis.load_trained_model") as load_model:
            with self.assertRaisesRegex(AudioAnalysisError, "WAV or MP3"):
                analyze_audio_bytes(b"data", "song.flac", Path("model.joblib"), ())

        load_model.assert_not_called()

    def test_successful_analysis_removes_temporary_uploaded_audio(self) -> None:
        temporary_paths: list[Path] = []

        def load_features(path: Path) -> AudioFeatures:
            self.assertTrue(path.is_file())
            temporary_paths.append(path)
            return self.features

        with (
            patch("cadence.song_analysis.load_trained_model", return_value=object()),
            patch(
                "cadence.song_analysis.load_audio_features",
                side_effect=load_features,
            ),
            patch(
                "cadence.song_analysis.estimate_song_metadata",
                return_value=self.metadata,
            ),
            patch(
                "cadence.song_analysis.predict_chord_events",
                return_value=(ChordEvent(0.0, 1.0, "N", 0.0),),
            ),
        ):
            result = analyze_audio_bytes(
                b"test-audio",
                "song.wav",
                Path("model.joblib"),
                (),
            )

        self.assertEqual(result.metadata, self.metadata)
        self.assertEqual(len(temporary_paths), 1)
        self.assertFalse(temporary_paths[0].exists())

    def test_decode_failure_is_actionable_and_still_removes_temporary_audio(self) -> None:
        temporary_paths: list[Path] = []

        def fail_to_load(path: Path) -> AudioFeatures:
            temporary_paths.append(path)
            raise ValueError("decoder detail")

        with (
            patch("cadence.song_analysis.load_trained_model", return_value=object()),
            patch(
                "cadence.song_analysis.load_audio_features",
                side_effect=fail_to_load,
            ),
        ):
            with self.assertRaisesRegex(AudioAnalysisError, "could not read"):
                analyze_audio_bytes(
                    b"not-audio",
                    "song.mp3",
                    Path("model.joblib"),
                    (),
                )

        self.assertFalse(temporary_paths[0].exists())

    def test_prediction_failure_does_not_leave_an_analysis_result_or_audio_file(self) -> None:
        temporary_paths: list[Path] = []

        def load_features(path: Path) -> AudioFeatures:
            temporary_paths.append(path)
            return self.features

        with (
            patch("cadence.song_analysis.load_trained_model", return_value=object()),
            patch(
                "cadence.song_analysis.load_audio_features",
                side_effect=load_features,
            ),
            patch(
                "cadence.song_analysis.estimate_song_metadata",
                return_value=self.metadata,
            ),
            patch(
                "cadence.song_analysis.predict_chord_events",
                side_effect=ValueError("invalid model output"),
            ),
        ):
            with self.assertRaisesRegex(AudioAnalysisError, "Chord analysis failed"):
                analyze_audio_bytes(
                    b"test-audio",
                    "song.wav",
                    Path("model.joblib"),
                    (),
                )

        self.assertFalse(temporary_paths[0].exists())


if __name__ == "__main__":
    unittest.main()
