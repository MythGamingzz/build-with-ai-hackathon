import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from cadence.audio_features import AudioFeatures, SAMPLE_RATE
from cadence.song_metadata import (
    TIME_SIGNATURES,
    _MAJOR_PROFILE,
    _key_estimate,
    bar_beat_position,
    estimate_song_metadata,
)


class KeyEstimateTests(unittest.TestCase):
    def test_finds_the_key_profile_with_a_heuristic_strength(self) -> None:
        chroma = np.repeat(_MAJOR_PROFILE.astype(np.float32)[:, None], 8, axis=1)

        key, strength = _key_estimate(chroma)

        self.assertEqual(key, "C major")
        self.assertGreaterEqual(strength, 0)


class SongMetadataTests(unittest.TestCase):
    def test_estimates_tempo_and_a_common_meter_candidate(self) -> None:
        chroma = np.repeat(_MAJOR_PROFILE.astype(np.float32)[:, None], 16, axis=1)
        features = AudioFeatures(
            chroma=chroma,
            rms=np.ones(16 * 43, dtype=np.float32),
            sample_rate=SAMPLE_RATE,
            duration=16.0,
        )
        beat_frames = np.arange(0, 16 * 43, 43, dtype=np.int64)
        with tempfile.TemporaryDirectory() as directory:
            audio_path = Path(directory) / "sample.wav"
            audio_path.touch()
            with (
                patch(
                    "cadence.song_metadata.librosa.load",
                    return_value=(np.ones(SAMPLE_RATE * 16, dtype=np.float32), SAMPLE_RATE),
                ),
                patch(
                    "cadence.song_metadata.librosa.beat.beat_track",
                    return_value=(60.0, beat_frames),
                ),
            ):
                estimate = estimate_song_metadata(audio_path, features)

        self.assertEqual(estimate.key, "C major")
        self.assertAlmostEqual(estimate.tempo_bpm or 0, 60)
        self.assertIn(estimate.time_signature, TIME_SIGNATURES)
        self.assertEqual(len(estimate.beat_times), len(beat_frames))

    def test_uses_meter_denominator_for_bar_and_beat_positions(self) -> None:
        self.assertEqual(bar_beat_position(2.0, 120, "6/8"), (2, 3.0))
        self.assertEqual(bar_beat_position(4.0, 120, "4/4"), (3, 1.0))

    def test_rejects_invalid_alignment_metadata(self) -> None:
        with self.assertRaisesRegex(ValueError, "positive"):
            bar_beat_position(1.0, 0, "4/4")
        with self.assertRaisesRegex(ValueError, "Unsupported time signature"):
            bar_beat_position(1.0, 120, "5/7")


if __name__ == "__main__":
    unittest.main()
