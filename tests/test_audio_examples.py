import io
import unittest
import wave

import numpy as np

from cadence.audio_examples import generate_progression_wav


class SyntheticAudioTests(unittest.TestCase):
    def test_generates_playable_non_silent_pcm_wave(self) -> None:
        audio = generate_progression_wav([1, 6, 4, 5], key="C")

        with wave.open(io.BytesIO(audio), "rb") as wav_file:
            self.assertEqual(wav_file.getnchannels(), 1)
            self.assertEqual(wav_file.getsampwidth(), 2)
            self.assertEqual(wav_file.getframerate(), 22050)
            self.assertGreater(wav_file.getnframes(), 0)
            samples = np.frombuffer(wav_file.readframes(wav_file.getnframes()), dtype="<i2")

        self.assertGreater(np.max(np.abs(samples)), 0)

    def test_generates_audio_with_flat_spelling(self) -> None:
        audio = generate_progression_wav([4], key="Gb")

        with wave.open(io.BytesIO(audio), "rb") as wav_file:
            self.assertGreater(wav_file.getnframes(), 0)

    def test_default_audio_is_quieter_and_has_long_chord_changes(self) -> None:
        audio = generate_progression_wav([1, 6, 4, 5])

        with wave.open(io.BytesIO(audio), "rb") as wav_file:
            samples = np.frombuffer(
                wav_file.readframes(wav_file.getnframes()),
                dtype="<i2",
            )

        self.assertEqual(len(samples), round((4 * 1.25 + 3 * 0.55) * 22050))
        self.assertLessEqual(np.max(np.abs(samples)), round(0.23 * 32767))

    def test_piano_like_chord_decays_over_its_duration(self) -> None:
        audio = generate_progression_wav([1])

        with wave.open(io.BytesIO(audio), "rb") as wav_file:
            samples = np.frombuffer(
                wav_file.readframes(wav_file.getnframes()),
                dtype="<i2",
            )

        early = samples[round(0.1 * 22050) : round(0.3 * 22050)]
        late = samples[round(0.9 * 22050) : round(1.1 * 22050)]
        self.assertGreater(np.mean(np.abs(early)), np.mean(np.abs(late)))

    def test_inter_chord_gap_is_silent_and_chromatic_chords_render(self) -> None:
        audio = generate_progression_wav(
            [1, 3],
            qualities=["major", "major"],
            chord_seconds=0.3,
            gap_seconds=0.2,
        )

        with wave.open(io.BytesIO(audio), "rb") as wav_file:
            samples = np.frombuffer(
                wav_file.readframes(wav_file.getnframes()),
                dtype="<i2",
            )

        gap_start = round(0.3 * 22050)
        gap_end = gap_start + round(0.2 * 22050)
        self.assertTrue(np.all(samples[gap_start:gap_end] == 0))

    def test_rejects_invalid_progression_or_audio_settings(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least 8000 Hz"):
            generate_progression_wav([1, 5], sample_rate=4000)
        with self.assertRaisesRegex(ValueError, "integers from 1 through 7"):
            generate_progression_wav([1, 9])
        with self.assertRaisesRegex(ValueError, "finite and positive"):
            generate_progression_wav([1, 5], chord_seconds=float("nan"))
        with self.assertRaisesRegex(ValueError, "finite and non-negative"):
            generate_progression_wav([1, 5], gap_seconds=-0.1)


if __name__ == "__main__":
    unittest.main()
