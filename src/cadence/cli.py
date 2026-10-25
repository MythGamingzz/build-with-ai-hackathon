import argparse
import json
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import sys
from typing import Sequence
import wave

from cadence.chords import estimate_chords
from cadence.transcription import transcribe_words


def validate_wav(path: Path) -> str | None:
    if path.suffix.lower() != ".wav":
        return "Only WAV audio is supported in this experiment."
    try:
        with wave.open(str(path), "rb") as audio_file:
            if audio_file.getnframes() == 0:
                return "The WAV file contains no audio frames."
            if audio_file.getframerate() <= 0:
                return "The WAV file has an invalid sample rate."
    except (EOFError, OSError, wave.Error) as error:
        return f"Unable to read WAV audio: {error}"
    return None


def package_version(name: str) -> str:
    try:
        return version(name)
    except PackageNotFoundError:
        return "unknown"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Estimate sung words and chord changes from a local recording."
    )
    parser.add_argument("recording", type=Path, help="Path to a local audio recording")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output"),
        help="Directory where analysis.json will be written (default: output)",
    )
    parser.add_argument(
        "--language",
        help="Optional language code for sung words; omit to let the model detect it",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.recording.is_file():
        print(f"error: audio file not found: {args.recording}", file=sys.stderr)
        return 2

    validation_error = validate_wav(args.recording)
    if validation_error:
        print(f"error: {validation_error}", file=sys.stderr)
        return 2

    try:
        with wave.open(str(args.recording), "rb") as audio_file:
            duration = audio_file.getnframes() / audio_file.getframerate()
        lyrics, detected_language = transcribe_words(
            args.recording, language=args.language
        )
        chords = estimate_chords(args.recording)
        args.output.mkdir(parents=True, exist_ok=True)
        output_file = args.output / "analysis.json"
        result = {
            "recording": args.recording.name,
            "duration_seconds": duration,
            "language": detected_language,
            "tools": {
                "faster_whisper": package_version("faster-whisper"),
                "librosa": package_version("librosa"),
            },
            "lyrics": lyrics,
            "chords": chords,
            "warnings": [] if lyrics else ["No sung words were recognized."],
        }
        output_file.write_text(
            json.dumps(result, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    except (OSError, ValueError, wave.Error) as error:
        print(f"error: analysis failed: {error}", file=sys.stderr)
        return 1

    print(f"Analysis saved to {output_file}")
    return 0
