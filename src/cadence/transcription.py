from collections.abc import Iterable
from pathlib import Path
from typing import Any

from faster_whisper import WhisperModel


def normalize_segments(segments: Iterable[Any]) -> list[dict[str, float | str]]:
    timed_words: list[dict[str, float | str]] = []

    for segment in segments:
        words = getattr(segment, "words", None)
        if words:
            for word in words:
                if word.start is None or word.end is None:
                    continue
                text = word.word.strip()
                if text:
                    timed_words.append(
                        {
                            "start": float(word.start),
                            "end": float(word.end),
                            "text": text,
                            "granularity": "word",
                        }
                    )
        else:
            text = segment.text.strip()
            if segment.start is not None and segment.end is not None and text:
                timed_words.append(
                    {
                        "start": float(segment.start),
                        "end": float(segment.end),
                        "text": text,
                        "granularity": "segment",
                    }
                )

    return timed_words


def transcribe_words(
    audio_path: Path, model_name: str = "base", language: str | None = None
) -> tuple[list[dict[str, float | str]], str | None]:
    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    options: dict[str, str | bool] = {
        "word_timestamps": True,
        "vad_filter": False,
    }
    if language:
        options["language"] = language
    segments, info = model.transcribe(str(audio_path), **options)
    return normalize_segments(segments), info.language
