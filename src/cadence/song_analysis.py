import tempfile
from dataclasses import dataclass
from pathlib import Path

import audioread

from cadence.audio_features import AudioFeatures, load_audio_features
from cadence.chord_model import (
    ChordEvent,
    ChordModelError,
    load_trained_model,
    predict_chord_events,
)
from cadence.matching import ProgressionMatch, match_progression
from cadence.progression_data import Progression
from cadence.song_metadata import SongMetadataEstimate, estimate_song_metadata

SUPPORTED_AUDIO_SUFFIXES = {".mp3", ".wav"}


class AudioAnalysisError(RuntimeError):
    pass


@dataclass(frozen=True)
class SongAnalysis:
    events: tuple[ChordEvent, ...]
    metadata: SongMetadataEstimate
    duration: float
    progression_match: ProgressionMatch


def analyze_audio_bytes(
    audio_bytes: bytes,
    filename: str,
    model_path: Path,
    progressions: tuple[Progression, ...],
) -> SongAnalysis:
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_AUDIO_SUFFIXES:
        raise AudioAnalysisError("Choose an audio file in WAV or MP3 format.")
    if not audio_bytes:
        raise AudioAnalysisError("The selected audio file is empty.")

    model = load_trained_model(model_path)
    try:
        with tempfile.TemporaryDirectory(prefix="cadence-audio-") as temporary_directory:
            audio_path = Path(temporary_directory) / f"visitor-audio{suffix}"
            try:
                audio_path.write_bytes(audio_bytes)
                features: AudioFeatures = load_audio_features(audio_path)
                metadata = estimate_song_metadata(audio_path, features)
            except (
                audioread.NoBackendError,
                OSError,
                RuntimeError,
                ValueError,
            ) as exc:
                raise AudioAnalysisError(
                    "Cadence could not read this audio. Try a playable WAV or MP3 "
                    "file and check that it is not damaged."
                ) from exc

            try:
                events = predict_chord_events(features, model)
                progression_match = match_progression(
                    [event.label for event in events],
                    progressions,
                )
            except (RuntimeError, ValueError) as exc:
                raise AudioAnalysisError(
                    f"Chord analysis failed: {exc}. No results were kept; try again "
                    "or rebuild the local model."
                ) from exc
            return SongAnalysis(
                events=events,
                metadata=metadata,
                duration=features.duration,
                progression_match=progression_match,
            )
    except OSError as exc:
        raise AudioAnalysisError(
            "Cadence could not create or clean up its temporary local audio workspace."
        ) from exc
