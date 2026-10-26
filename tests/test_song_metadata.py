import math
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from cadence.audio_features import AudioFeatures, SAMPLE_RATE
from cadence.song_metadata import (
    _MAJOR_PROFILE,
    _key_estimate,
    _meter_estimate,
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
        self.assertEqual(estimate.time_signature, "4/4")
        self.assertEqual(estimate.meter_strength, 0.0)
        self.assertEqual(len(estimate.beat_times), len(beat_frames))

    def test_detects_clear_four_four_accent_pattern(self) -> None:
        duration = 24.0
        frame_seconds = 512 / SAMPLE_RATE
        rms = np.full(
            math.ceil(duration / frame_seconds),
            0.1,
            dtype=np.float32,
        )
        eighth_seconds = 0.25
        bar_pattern = (1.0, 0.1, 0.45, 0.1, 0.8, 0.1, 0.45, 0.1)
        for index, amplitude in enumerate(
            bar_pattern * int(duration / (eighth_seconds * len(bar_pattern)))
        ):
            frame = round(index * eighth_seconds / frame_seconds)
            rms[frame] = amplitude

        meter, strength = _meter_estimate(
            rms,
            duration,
            120.0,
            tuple(index * 0.5 for index in range(48)),
        )

        self.assertEqual(meter, "4/4")
        self.assertGreater(strength, 0.05)

    def test_preserves_clear_three_four_and_six_eight_patterns(self) -> None:
        frame_seconds = 512 / SAMPLE_RATE
        duration = 24.0
        for expected_meter, pattern in (
            ("3/4", (1.0, 0.1, 0.65, 0.1, 0.5, 0.1)),
            ("6/8", (1.0, 0.1, 0.1, 0.7, 0.1, 0.1)),
        ):
            with self.subTest(expected_meter=expected_meter):
                rms = np.full(
                    math.ceil(duration / frame_seconds),
                    0.1,
                    dtype=np.float32,
                )
                for index, amplitude in enumerate(pattern * 16):
                    time = index * 0.25
                    if time >= duration:
                        break
                    rms[round(time / frame_seconds)] = amplitude

                meter, strength = _meter_estimate(
                    rms,
                    duration,
                    120.0,
                    tuple(index * 0.5 for index in range(48)),
                )

                self.assertEqual(meter, expected_meter)
                self.assertGreater(strength, 0.05)

    def test_detects_six_eight_from_fast_eighth_note_pulses(self) -> None:
        duration = 24.0
        frame_seconds = 512 / SAMPLE_RATE
        frame_count = math.ceil(duration / frame_seconds)
        rms = np.full(frame_count, 0.1, dtype=np.float32)
        beat_frames = np.arange(0, frame_count, 14, dtype=np.int64)
        pattern = (1.0, 0.1, 0.1, 0.7, 0.1, 0.1)
        for index, frame in enumerate(beat_frames):
            rms[frame] = pattern[index % len(pattern)]
        features = AudioFeatures(
            chroma=np.repeat(_MAJOR_PROFILE.astype(np.float32)[:, None], frame_count, axis=1),
            rms=rms,
            sample_rate=SAMPLE_RATE,
            duration=duration,
        )
        with tempfile.TemporaryDirectory() as directory:
            audio_path = Path(directory) / "six-eight.wav"
            audio_path.touch()
            with (
                patch(
                    "cadence.song_metadata.librosa.load",
                    return_value=(
                        np.ones(SAMPLE_RATE * int(duration), dtype=np.float32),
                        SAMPLE_RATE,
                    ),
                ),
                patch(
                    "cadence.song_metadata.librosa.beat.beat_track",
                    return_value=(180.0, beat_frames),
                ),
            ):
                estimate = estimate_song_metadata(audio_path, features)

        self.assertEqual(estimate.time_signature, "6/8")
        self.assertAlmostEqual(estimate.tempo_bpm or 0, 90.0)

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
