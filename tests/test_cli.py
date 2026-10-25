from pathlib import Path
import tempfile
import unittest
import wave

from cadence.cli import validate_wav


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


if __name__ == "__main__":
    unittest.main()
