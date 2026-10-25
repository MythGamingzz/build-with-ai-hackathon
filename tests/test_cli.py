import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import wave

from cadence.cli import main, validate_wav


class WavValidationTests(unittest.TestCase):
    def test_rejects_non_wav_files(self) -> None:
        self.assertIn("Only WAV", validate_wav(Path("song.mp3")))

    def test_rejects_malformed_wav_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.wav"
            path.write_bytes(b"not a wav file")

            self.assertIn("Unable to read WAV", validate_wav(path))

    def test_accepts_nonempty_pcm_wav(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.wav"
            with wave.open(str(path), "wb") as audio_file:
                audio_file.setnchannels(1)
                audio_file.setsampwidth(2)
                audio_file.setframerate(22050)
                audio_file.writeframes(b"\0\0" * 10)

            self.assertIsNone(validate_wav(path))


class ReferenceCliTests(unittest.TestCase):
    def create_wav(self, path: Path) -> None:
        with wave.open(str(path), "wb") as audio_file:
            audio_file.setnchannels(1)
            audio_file.setsampwidth(2)
            audio_file.setframerate(10)
            audio_file.writeframes(b"\0\0" * 10)

    def test_keeps_raw_predictions_separate_from_reference_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            recording = root / "sample.wav"
            reference = root / "reference.json"
            output = root / "output"
            self.create_wav(recording)
            reference.write_text(
                json.dumps(
                    {
                        "recording": recording.name,
                        "lyrics": [
                            {"start": 0.2, "end": 0.8, "text": "correct"}
                        ],
                        "chords": [
                            {"start": 0.0, "end": 1.0, "label": "E"}
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with (
                patch(
                    "cadence.cli.transcribe_words",
                    return_value=([{"start": 0.2, "end": 0.8, "text": "raw"}], "en"),
                ),
                patch(
                    "cadence.cli.estimate_chords",
                    return_value=[{"start": 0.0, "end": 1.0, "label": "C#m"}],
                ),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                exit_code = main(
                    [
                        str(recording),
                        "--reference",
                        str(reference),
                        "--output",
                        str(output),
                    ]
                )

            saved = json.loads((output / "analysis.json").read_text(encoding="utf-8"))
            report = (output / "report.html").read_text(encoding="utf-8")

        self.assertEqual(exit_code, 0)
        self.assertEqual(saved["lyrics"][0]["text"], "raw")
        self.assertIn("raw", report)
        self.assertIn("correct", report)
        self.assertIn("Mismatch", report)

    def test_invalid_reference_fails_before_running_analysis(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            recording = root / "sample.wav"
            reference = root / "reference.json"
            self.create_wav(recording)
            reference.write_text(
                json.dumps(
                    {"recording": "another.wav", "lyrics": [], "chords": []}
                ),
                encoding="utf-8",
            )

            with (
                patch("cadence.cli.transcribe_words") as transcribe,
                contextlib.redirect_stderr(io.StringIO()),
            ):
                exit_code = main(
                    [str(recording), "--reference", str(reference)]
                )

        self.assertEqual(exit_code, 1)
        transcribe.assert_not_called()


if __name__ == "__main__":
    unittest.main()
