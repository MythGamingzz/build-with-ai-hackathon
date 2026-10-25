from types import SimpleNamespace
import unittest
from pathlib import Path
from unittest.mock import patch

from cadence.transcription import normalize_segments, transcribe_words


class TranscriptionNormalizationTests(unittest.TestCase):
    def test_uses_word_timestamps_when_available(self) -> None:
        segments = [
            SimpleNamespace(
                words=[
                    SimpleNamespace(start=0.1, end=0.4, word=" hello ", probability=0.9),
                    SimpleNamespace(start=0.5, end=0.7, word="world", probability=0.8),
                ],
                text=" hello world",
            )
        ]

        words = normalize_segments(segments)

        self.assertEqual([word["text"] for word in words], ["hello", "world"])
        self.assertEqual([word["granularity"] for word in words], ["word", "word"])
        self.assertEqual(words[0]["start"], 0.1)

    def test_keeps_segment_timing_when_word_timestamps_are_unavailable(self) -> None:
        segments = [
            SimpleNamespace(
                words=None,
                start=1.0,
                end=2.0,
                text=" sung phrase ",
            )
        ]

        words = normalize_segments(segments)

        self.assertEqual(
            words,
            [
                {
                    "start": 1.0,
                    "end": 2.0,
                    "text": "sung phrase",
                    "granularity": "segment",
                }
            ],
        )

    @patch("cadence.transcription.WhisperModel")
    def test_forwards_an_explicit_language_hint(self, model_factory) -> None:
        model = model_factory.return_value
        model.transcribe.return_value = (
            [],
            SimpleNamespace(language="id"),
        )

        words, language = transcribe_words(Path("recording.wav"), language="id")

        model.transcribe.assert_called_once_with(
            "recording.wav",
            word_timestamps=True,
            vad_filter=False,
            language="id",
        )
        self.assertEqual(words, [])
        self.assertEqual(language, "id")

    @patch("cadence.transcription.WhisperModel")
    def test_keeps_automatic_language_detection_as_the_default(
        self, model_factory
    ) -> None:
        model = model_factory.return_value
        model.transcribe.return_value = (
            [],
            SimpleNamespace(language="en"),
        )

        transcribe_words(Path("recording.wav"))

        model.transcribe.assert_called_once_with(
            "recording.wav",
            word_timestamps=True,
            vad_filter=False,
        )


if __name__ == "__main__":
    unittest.main()
