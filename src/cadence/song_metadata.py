from dataclasses import dataclass
from pathlib import Path

import librosa
import numpy as np
from numpy.typing import NDArray

from cadence.audio_features import HOP_LENGTH, SAMPLE_RATE, AudioFeatures

NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
KEY_CHOICES = tuple(
    [f"{note} major" for note in NOTE_NAMES]
    + [f"{note} minor" for note in NOTE_NAMES]
)
TIME_SIGNATURES = ("3/4", "4/4", "6/8")
_MAJOR_PROFILE = np.array(
    [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88],
    dtype=np.float64,
)
_MINOR_PROFILE = np.array(
    [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17],
    dtype=np.float64,
)


@dataclass(frozen=True)
class SongMetadataEstimate:
    key: str
    key_strength: float
    tempo_bpm: float | None
    tempo_strength: float
    time_signature: str
    meter_strength: float
    beat_times: tuple[float, ...]


def _key_estimate(chroma: NDArray[np.float32]) -> tuple[str, float]:
    if chroma.ndim != 2 or chroma.shape[0] != 12 or chroma.shape[1] == 0:
        raise ValueError("Key estimation requires non-empty 12-bin chroma features.")

    profile = np.mean(chroma, axis=1).astype(np.float64)
    if np.ptp(profile) <= np.finfo(np.float64).eps:
        return "C major", 0.0
    profile = (profile - np.mean(profile)) / (np.std(profile) or 1.0)

    candidates = []
    for mode, template in (("major", _MAJOR_PROFILE), ("minor", _MINOR_PROFILE)):
        normalized_template = (template - np.mean(template)) / np.std(template)
        for tonic, note in enumerate(NOTE_NAMES):
            score = float(np.dot(profile, np.roll(normalized_template, tonic)) / 12)
            candidates.append((score, f"{note} {mode}"))
    candidates.sort(reverse=True)
    strength = max(0.0, candidates[0][0] - candidates[1][0])
    return candidates[0][1], strength


def _tempo_estimate(audio: NDArray[np.float32]) -> tuple[float | None, tuple[float, ...], float]:
    tempo_values, beat_frames = librosa.beat.beat_track(
        y=audio,
        sr=SAMPLE_RATE,
        hop_length=HOP_LENGTH,
        trim=False,
    )
    tempo_array = np.asarray(tempo_values, dtype=np.float64).reshape(-1)
    tempo = float(tempo_array[0]) if tempo_array.size else 0.0
    beat_times_array = librosa.frames_to_time(
        beat_frames,
        sr=SAMPLE_RATE,
        hop_length=HOP_LENGTH,
    )
    beat_times = tuple(float(value) for value in beat_times_array)
    if (not np.isfinite(tempo) or tempo < 30 or tempo > 300) and len(beat_times) > 1:
        intervals = np.diff(beat_times)
        median_interval = float(np.median(intervals))
        tempo = 60.0 / median_interval if median_interval > 0 else 0.0
    if not np.isfinite(tempo) or tempo < 30 or tempo > 300:
        return None, beat_times, 0.0

    if len(beat_times) < 3:
        return tempo, beat_times, 0.0
    intervals = np.diff(beat_times)
    variability = float(np.std(intervals) / max(float(np.mean(intervals)), 1e-9))
    strength = max(0.0, min(1.0, 1.0 - 2.0 * variability))
    return tempo, beat_times, strength


def _meter_estimate(
    rms: NDArray[np.float32],
    duration: float,
    tempo_bpm: float | None,
    beat_times: tuple[float, ...],
) -> tuple[str, float]:
    if tempo_bpm is None or not beat_times:
        return "4/4", 0.0

    eighth_seconds = 30.0 / tempo_bpm
    first_beat = beat_times[0]
    sample_times = np.arange(first_beat, duration, eighth_seconds)
    if sample_times.size < 12:
        return "4/4", 0.0

    frame_times = np.arange(rms.size) * HOP_LENGTH / SAMPLE_RATE
    accents = np.interp(sample_times, frame_times, rms)
    meter_layouts = {
        "3/4": (6, (0, 2, 4)),
        "4/4": (8, (0, 2, 4, 6)),
        "6/8": (6, (0, 3)),
    }
    scores = []
    for signature, (subdivisions, strong_positions) in meter_layouts.items():
        full_bars = accents.size // subdivisions
        if full_bars < 2:
            scores.append((signature, float("-inf")))
            continue
        bar_values = accents[: full_bars * subdivisions].reshape(
            full_bars, subdivisions
        )
        strong = np.mean(bar_values[:, strong_positions])
        weak_positions = tuple(
            position
            for position in range(subdivisions)
            if position not in strong_positions
        )
        weak = np.mean(bar_values[:, weak_positions])
        scores.append(
            (
                signature,
                float((strong - weak) / max(float(np.max(bar_values)), 1e-9)),
            )
        )

    scores.sort(key=lambda item: item[1], reverse=True)
    if not np.isfinite(scores[0][1]):
        return "4/4", 0.0
    margin = scores[0][1] - scores[1][1]
    return scores[0][0], max(0.0, min(1.0, float(margin)))


def estimate_song_metadata(
    audio_path: Path,
    features: AudioFeatures,
) -> SongMetadataEstimate:
    audio, _ = librosa.load(audio_path, sr=SAMPLE_RATE, mono=True)
    if audio.size == 0:
        raise ValueError(f"The audio file contains no samples: {audio_path}")

    key, key_strength = _key_estimate(features.chroma)
    tempo, beat_times, tempo_strength = _tempo_estimate(audio)
    meter, meter_strength = _meter_estimate(
        features.rms,
        features.duration,
        tempo,
        beat_times,
    )
    return SongMetadataEstimate(
        key=key,
        key_strength=key_strength,
        tempo_bpm=tempo,
        tempo_strength=tempo_strength,
        time_signature=meter,
        meter_strength=meter_strength,
        beat_times=beat_times,
    )


def bar_beat_position(
    event_time: float,
    tempo_bpm: float,
    time_signature: str,
    first_beat_time: float = 0.0,
) -> tuple[int, float]:
    if not np.isfinite(tempo_bpm) or tempo_bpm <= 0:
        raise ValueError("Tempo must be a positive finite number.")
    try:
        numerator_text, denominator_text = time_signature.split("/", maxsplit=1)
        numerator = int(numerator_text)
        denominator = int(denominator_text)
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError(f"Unsupported time signature: {time_signature!r}.") from exc
    if numerator < 1 or denominator not in {2, 4, 8, 16}:
        raise ValueError(f"Unsupported time signature: {time_signature!r}.")

    seconds_per_beat = 60.0 / tempo_bpm * 4.0 / denominator
    elapsed_beats = max(0.0, event_time - first_beat_time) / seconds_per_beat
    bar_index = int(elapsed_beats // numerator)
    beat = elapsed_beats - bar_index * numerator + 1
    return bar_index + 1, round(beat, 2)
