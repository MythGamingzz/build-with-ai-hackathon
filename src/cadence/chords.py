from pathlib import Path

import librosa
import numpy as np
from scipy.ndimage import uniform_filter1d
from numpy.typing import NDArray

SAMPLE_RATE = 22050
HOP_LENGTH = 512
CHROMA_AVERAGE_FRAMES = 21
LABEL_SMOOTHING_FRAMES = 21
MIN_CHORD_SECONDS = 0.4
MIN_RELATIVE_RMS = 0.001
NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
CHORD_QUALITIES = {
    "major": (0, 4, 7),
    "minor": (0, 3, 7),
}
CHORD_LABELS = tuple(
    f"{root}{'m' if quality == 'minor' else ''}"
    for root in NOTE_NAMES
    for quality in CHORD_QUALITIES
)
NO_CHORD_INDEX = len(CHORD_LABELS)
NO_CHORD_LABEL = "N"


def chord_templates() -> NDArray[np.float32]:
    templates = np.zeros((len(CHORD_LABELS), 12), dtype=np.float32)
    index = 0
    for root in range(12):
        for intervals in CHORD_QUALITIES.values():
            templates[index, [(root + interval) % 12 for interval in intervals]] = 1
            index += 1
    norms = np.linalg.norm(templates, axis=1, keepdims=True)
    return templates / norms


def classify_chroma(
    chroma: NDArray[np.floating],
) -> tuple[NDArray[np.int64], NDArray[np.float32]]:
    if chroma.ndim != 2 or chroma.shape[0] != 12 or chroma.shape[1] == 0:
        raise ValueError("Expected a 12-bin chroma matrix with at least one frame.")

    frame_norms = np.linalg.norm(chroma, axis=0, keepdims=True)
    normalized = chroma / np.maximum(frame_norms, np.finfo(np.float32).eps)
    scores = chord_templates() @ normalized
    labels = np.argmax(scores, axis=0).astype(np.int64)
    labels[frame_norms[0] <= 1e-6] = NO_CHORD_INDEX
    return labels, scores.astype(np.float32)


def smooth_labels(labels: NDArray[np.int64], window_size: int = 5) -> NDArray[np.int64]:
    if window_size < 1 or window_size % 2 == 0:
        raise ValueError("The smoothing window must be a positive odd number.")
    if labels.size == 0:
        return labels.copy()

    radius = window_size // 2
    padded = np.pad(labels, (radius, radius), mode="edge")
    smoothed = np.empty_like(labels)
    for index in range(labels.size):
        counts = np.bincount(
            padded[index : index + window_size], minlength=NO_CHORD_INDEX + 1
        )
        smoothed[index] = int(np.argmax(counts))
    return smoothed


def merge_short_runs(
    labels: NDArray[np.int64], minimum_frames: int
) -> NDArray[np.int64]:
    if minimum_frames < 1:
        raise ValueError("The minimum chord duration must be positive.")

    merged = labels.copy()
    while merged.size:
        boundaries = np.flatnonzero(np.diff(merged) != 0) + 1
        starts = np.concatenate(([0], boundaries))
        ends = np.concatenate((boundaries, [merged.size]))
        lengths = ends - starts
        short_runs = np.flatnonzero(lengths < minimum_frames)
        if short_runs.size == 0 or starts.size == 1:
            break

        run_index = int(short_runs[np.argmin(lengths[short_runs])])
        if run_index == 0:
            neighbor_index = 1
        elif run_index == starts.size - 1:
            neighbor_index = run_index - 1
        else:
            neighbor_index = (
                run_index - 1
                if lengths[run_index - 1] >= lengths[run_index + 1]
                else run_index + 1
            )
        merged[starts[run_index] : ends[run_index]] = merged[starts[neighbor_index]]

    return merged


def mask_low_energy_frames(
    labels: NDArray[np.int64],
    rms: NDArray[np.floating],
    relative_threshold: float = MIN_RELATIVE_RMS,
) -> NDArray[np.int64]:
    if labels.size != rms.size:
        raise ValueError("Chord labels and RMS values must have equal lengths.")
    if relative_threshold < 0:
        raise ValueError("The relative RMS threshold cannot be negative.")
    if rms.size == 0:
        return labels.copy()

    threshold = float(np.max(rms)) * relative_threshold
    masked = labels.copy()
    masked[rms <= threshold] = NO_CHORD_INDEX
    return masked


def chord_events(
    labels: NDArray[np.int64],
    scores: NDArray[np.float32],
    frame_seconds: float,
    duration: float,
) -> list[dict[str, float | str]]:
    if scores.shape != (len(CHORD_LABELS), labels.size):
        raise ValueError("Chord scores must contain one score per chord and frame.")
    if frame_seconds <= 0 or duration <= 0:
        raise ValueError("Frame duration and audio duration must be positive.")
    if labels.size == 0:
        return []

    boundaries = np.flatnonzero(np.diff(labels) != 0) + 1
    starts = np.concatenate(([0], boundaries))
    ends = np.concatenate((boundaries, [labels.size]))
    events: list[dict[str, float | str]] = []

    for start_frame, end_frame in zip(starts, ends, strict=True):
        start_time = min(float(start_frame * frame_seconds), duration)
        end_time = min(float(end_frame * frame_seconds), duration)
        if end_time <= start_time:
            continue
        chord_index = int(labels[start_frame])
        is_silence = chord_index == NO_CHORD_INDEX
        events.append(
            {
                "start": start_time,
                "end": end_time,
                "label": NO_CHORD_LABEL if is_silence else CHORD_LABELS[chord_index],
                "confidence": 0.0
                if is_silence
                else float(np.mean(scores[chord_index, start_frame:end_frame])),
            }
        )

    return events


def estimate_chords(audio_path: Path) -> list[dict[str, float | str]]:
    audio, sample_rate = librosa.load(audio_path, sr=SAMPLE_RATE, mono=True)
    if audio.size == 0:
        raise ValueError("The audio file contains no samples.")

    chroma = librosa.feature.chroma_cqt(
        y=audio,
        sr=sample_rate,
        hop_length=HOP_LENGTH,
    )
    chroma = uniform_filter1d(
        chroma,
        size=CHROMA_AVERAGE_FRAMES,
        axis=1,
        mode="nearest",
    )
    rms = librosa.feature.rms(
        y=audio,
        frame_length=2048,
        hop_length=HOP_LENGTH,
    )[0]
    labels, scores = classify_chroma(chroma)
    labels = smooth_labels(labels, LABEL_SMOOTHING_FRAMES)
    minimum_frames = round(MIN_CHORD_SECONDS * sample_rate / HOP_LENGTH)
    labels = merge_short_runs(labels, minimum_frames)
    labels = mask_low_energy_frames(labels, rms)
    return chord_events(
        labels,
        scores,
        frame_seconds=HOP_LENGTH / sample_rate,
        duration=len(audio) / sample_rate,
    )
