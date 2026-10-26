import argparse
import csv
import hashlib
import json
import math
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

import joblib
import numpy as np
from numpy.typing import NDArray
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score

from cadence.audio_features import (
    HOP_LENGTH,
    AudioFeatures,
    load_audio_features,
)
from cadence.chords import (
    CHORD_LABELS,
    LABEL_SMOOTHING_FRAMES,
    MIN_CHORD_SECONDS,
    NO_CHORD_INDEX,
    NO_CHORD_LABEL,
    classify_chroma,
    mask_low_energy_frames,
    merge_short_runs,
    postprocess_model_labels,
    smooth_labels,
)
from cadence.feedback import feedback_annotation_paths

ANNOTATION_FIELDS = {
    "song_id",
    "audio_path",
    "start_seconds",
    "end_seconds",
    "chord_label",
}
DEFAULT_ROOT = Path(__file__).resolve().parents[2]
_ROOT_NORMALIZATION = {
    "Cb": "B",
    "Db": "C#",
    "Eb": "D#",
    "Fb": "E",
    "Gb": "F#",
    "Ab": "G#",
    "Bb": "A#",
    "E#": "F",
    "B#": "C",
}
_NOTE_PATTERN = re.compile(r"^([A-Ga-g])([#b]?)(.*)$")


@dataclass(frozen=True)
class Annotation:
    song_id: str
    audio_path: Path
    start_seconds: float
    end_seconds: float
    chord_label: str


@dataclass(frozen=True)
class SongSplit:
    training_song_ids: tuple[str, ...]
    held_out_song_id: str


@dataclass(frozen=True)
class MetricSummary:
    accuracy: float
    macro_f1: float
    frame_count: int


@dataclass(frozen=True)
class TrainingReport:
    model_path: Path
    split: SongSplit
    training_labels: tuple[str, ...]
    held_out_labels: tuple[str, ...]
    unsupported_labels: tuple[tuple[str, int], ...]
    model_metrics: MetricSummary
    baseline_metrics: MetricSummary
    augmented_song_count: int
    feedback_song_ids: tuple[str, ...]


def normalize_chord_label(value: str) -> str:
    label = re.sub(r"\s*\([^)]*\)\s*$", "", value.strip()).strip()
    no_chord = label.lower().replace("-", " ").strip()
    if no_chord in {"n", "no chord", "no chords", "chordless"}:
        return NO_CHORD_LABEL

    chord = label.split("/", maxsplit=1)[0].strip()
    match = _NOTE_PATTERN.fullmatch(chord)
    if not match:
        raise ValueError(f"Unsupported chord label: {value!r}")

    root = f"{match.group(1).upper()}{match.group(2)}"
    root = _ROOT_NORMALIZATION.get(root, root)
    suffix = match.group(3).strip().lower().replace(" ", "")

    if suffix in {"", "maj", "major", "6", "7", "maj6", "maj7", "major6", "major7"}:
        return root
    if suffix in {"m", "min", "minor", "m6", "m7", "min6", "min7", "minor6", "minor7"}:
        return f"{root}m"
    if suffix in {"aug", "+", "augmented"}:
        return f"{root}aug"
    raise ValueError(f"Unsupported chord quality in {value!r}")


def read_annotations(path: Path, root: Path = DEFAULT_ROOT) -> list[Annotation]:
    annotations: list[Annotation] = []
    root = root.resolve()

    with path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None:
            raise ValueError(f"Annotation CSV has no header: {path}")
        missing = ANNOTATION_FIELDS.difference(reader.fieldnames)
        if missing:
            raise ValueError(
                f"Annotation CSV is missing columns: {', '.join(sorted(missing))}"
            )

        for row_number, row in enumerate(reader, start=2):
            try:
                song_id = row["song_id"].strip()
                audio_path_value = Path(row["audio_path"].strip())
                start = float(row["start_seconds"])
                end = float(row["end_seconds"])
                chord = normalize_chord_label(row["chord_label"])
            except (AttributeError, TypeError, ValueError) as exc:
                raise ValueError(
                    f"Invalid annotation at {path}, row {row_number}: {exc}"
                ) from exc

            if not song_id:
                raise ValueError(f"Empty song_id at {path}, row {row_number}.")
            if audio_path_value.is_absolute():
                raise ValueError(
                    f"Audio path must be relative to the project root at "
                    f"{path}, row {row_number}."
                )
            audio_path = (root / audio_path_value).resolve()
            if not audio_path.is_relative_to(root):
                raise ValueError(
                    f"Audio path escapes the project root at {path}, row {row_number}."
                )
            if not math.isfinite(start) or not math.isfinite(end) or start < 0 or end <= start:
                raise ValueError(
                    f"Annotation times must be finite and end after start at "
                    f"{path}, row {row_number}."
                )
            annotations.append(
                Annotation(song_id, audio_path, start, end, chord)
            )

    if not annotations:
        raise ValueError(f"No annotations found in {path}")

    annotations.sort(key=lambda annotation: (annotation.song_id, annotation.start_seconds))
    prior_by_song: dict[str, Annotation] = {}
    audio_by_song: dict[str, Path] = {}
    for annotation in annotations:
        prior = prior_by_song.get(annotation.song_id)
        if prior and annotation.start_seconds < prior.end_seconds:
            raise ValueError(
                f"Overlapping annotation intervals for {annotation.song_id}: "
                f"{prior.start_seconds:.3f}-{prior.end_seconds:.3f} and "
                f"{annotation.start_seconds:.3f}-{annotation.end_seconds:.3f}."
            )
        previous_audio = audio_by_song.setdefault(annotation.song_id, annotation.audio_path)
        if previous_audio != annotation.audio_path:
            raise ValueError(
                f"Song {annotation.song_id} refers to more than one audio file."
            )
        prior_by_song[annotation.song_id] = annotation

    return annotations


def read_split(path: Path) -> SongSplit:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        training_value = data["training_song_ids"]
        if not isinstance(training_value, list):
            raise TypeError("training_song_ids must be a list")
        training = tuple(training_value)
        held_out = data["held_out_song_id"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise ValueError(f"Invalid training split file {path}: {exc}") from exc

    if not training or any(not isinstance(song_id, str) or not song_id for song_id in training):
        raise ValueError("The training split must list one or more song IDs.")
    if not isinstance(held_out, str) or not held_out:
        raise ValueError("The split must name one held-out song ID.")
    if len(set(training)) != len(training):
        raise ValueError("The training split contains duplicate song IDs.")
    if held_out in training:
        raise ValueError("A song cannot appear in both training and holdout.")
    return SongSplit(training, held_out)


def _file_sha256(path: Path) -> bytes:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.digest()


def _normalized_features(chroma: NDArray[np.float32]) -> NDArray[np.float32]:
    norms = np.linalg.norm(chroma, axis=0, keepdims=True)
    return (chroma / np.maximum(norms, np.finfo(np.float32).eps)).T.astype(
        np.float32
    )


def _baseline_labels(features: AudioFeatures) -> NDArray[np.str_]:
    labels, _ = classify_chroma(features.chroma)
    labels = smooth_labels(labels, LABEL_SMOOTHING_FRAMES)
    minimum_frames = round(MIN_CHORD_SECONDS * features.sample_rate / HOP_LENGTH)
    labels = merge_short_runs(labels, minimum_frames)
    labels = mask_low_energy_frames(labels, features.rms)
    return np.array(
        [
            NO_CHORD_LABEL if label == NO_CHORD_INDEX else CHORD_LABELS[int(label)]
            for label in labels
        ],
        dtype="<U8",
    )


def _postprocess_model_labels(
    predictions: NDArray[np.str_],
    features: AudioFeatures,
) -> NDArray[np.str_]:
    return postprocess_model_labels(predictions, features)


def _score(
    reference: NDArray[np.str_],
    predictions: NDArray[np.str_],
) -> MetricSummary:
    labels = sorted(set(reference.tolist()) | set(predictions.tolist()))
    return MetricSummary(
        accuracy=float(accuracy_score(reference, predictions)),
        macro_f1=float(
            f1_score(reference, predictions, labels=labels, average="macro", zero_division=0)
        ),
        frame_count=int(reference.size),
    )


def train_and_evaluate(
    annotations_path: Path,
    split_path: Path,
    model_path: Path,
    root: Path = DEFAULT_ROOT,
    feature_loader: Callable[[Path], AudioFeatures] = load_audio_features,
    feedback_paths: Sequence[Path] = (),
) -> TrainingReport:
    annotations = read_annotations(annotations_path, root)
    annotated_songs = {annotation.song_id for annotation in annotations}
    feedback_song_ids: set[str] = set()
    for feedback_path in feedback_paths:
        feedback_annotations = read_annotations(feedback_path, root)
        feedback_ids = {
            annotation.song_id for annotation in feedback_annotations
        }
        if len(feedback_ids) != 1:
            raise ValueError(
                f"Feedback manifest must contain exactly one song: "
                f"{feedback_path}."
            )
        feedback_id = next(iter(feedback_ids))
        if not feedback_id.startswith("feedback_"):
            raise ValueError(
                f"Feedback song IDs must start with 'feedback_': {feedback_id}."
            )
        if feedback_id in annotated_songs or feedback_id in feedback_song_ids:
            raise ValueError(f"Duplicate feedback song ID: {feedback_id}.")
        feedback_song_ids.add(feedback_id)
        annotated_songs.add(feedback_id)
        annotations.extend(feedback_annotations)

    split = read_split(split_path)
    held_out_feedback = feedback_song_ids.intersection({split.held_out_song_id})
    if held_out_feedback:
        raise ValueError(
            "Feedback cannot be assigned to the held-out song: "
            + ", ".join(sorted(held_out_feedback))
            + ". Keep the original evaluation song held out."
        )
    unassigned_feedback = feedback_song_ids.difference(split.training_song_ids)
    if unassigned_feedback:
        raise ValueError(
            "Review feedback and add these song IDs to training_song_ids in "
            f"{split_path} before including them: "
            + ", ".join(sorted(unassigned_feedback))
        )

    expected_songs = set(split.training_song_ids) | {split.held_out_song_id}
    if annotated_songs != expected_songs:
        missing = expected_songs - annotated_songs
        extra = annotated_songs - expected_songs
        details = []
        if missing:
            details.append(f"missing annotations for {', '.join(sorted(missing))}")
        if extra:
            details.append(f"unassigned songs {', '.join(sorted(extra))}")
        raise ValueError("Training split does not match annotations: " + "; ".join(details))

    if feedback_song_ids:
        held_out_audio = next(
            annotation.audio_path
            for annotation in annotations
            if annotation.song_id == split.held_out_song_id
        )
        held_out_digest = _file_sha256(held_out_audio)
        for feedback_id in sorted(feedback_song_ids):
            feedback_audio = next(
                annotation.audio_path
                for annotation in annotations
                if annotation.song_id == feedback_id
            )
            if _file_sha256(feedback_audio) == held_out_digest:
                raise ValueError(
                    f"Feedback audio for {feedback_id} is identical to the "
                    "held-out recording. Keep it out of training."
                )

    frames_by_song: dict[str, tuple[NDArray[np.float32], NDArray[np.str_]]] = {}
    features_by_song: dict[str, AudioFeatures] = {}
    song_ids = sorted(annotated_songs)
    for song_id in song_ids:
        song_annotations = [
            annotation for annotation in annotations if annotation.song_id == song_id
        ]
        audio_path = song_annotations[0].audio_path
        if not audio_path.is_file():
            raise ValueError(f"Training audio file is missing: {audio_path}")
        features = feature_loader(audio_path)
        frame_seconds = HOP_LENGTH / features.sample_rate
        frame_times = np.arange(features.chroma.shape[1]) * frame_seconds
        frame_labels = np.full(frame_times.size, "", dtype="<U8")
        for annotation in song_annotations:
            if annotation.end_seconds > features.duration + frame_seconds:
                raise ValueError(
                    f"Annotation for {song_id} ends at {annotation.end_seconds:.3f}s, "
                    f"past the {features.duration:.3f}s audio length."
                )
            selected = (frame_times >= annotation.start_seconds) & (
                frame_times < annotation.end_seconds
            )
            if np.any(frame_labels[selected] != ""):
                raise ValueError(f"Overlapping annotation frames for {song_id}.")
            frame_labels[selected] = annotation.chord_label
        labeled = frame_labels != ""
        if not np.any(labeled):
            raise ValueError(f"No audio frames are covered by labels for {song_id}.")
        frames_by_song[song_id] = (
            _normalized_features(features.chroma)[labeled],
            frame_labels[labeled],
        )
        features_by_song[song_id] = features

    training_features = np.concatenate(
        [frames_by_song[song_id][0] for song_id in split.training_song_ids]
    )
    training_labels = np.concatenate(
        [frames_by_song[song_id][1] for song_id in split.training_song_ids]
    )
    if np.unique(training_labels).size < 2:
        raise ValueError("Training requires at least two distinct chord labels.")

    model = LogisticRegression(max_iter=2000, random_state=0)
    model.fit(training_features, training_labels)

    _, held_out_labels = frames_by_song[split.held_out_song_id]
    held_out_audio = features_by_song[split.held_out_song_id]
    all_model_predictions = model.predict(
        _normalized_features(held_out_audio.chroma)
    ).astype("<U8")
    all_model_predictions = _postprocess_model_labels(
        all_model_predictions,
        held_out_audio,
    )
    all_baseline_labels = _baseline_labels(held_out_audio)
    annotation_mask = np.zeros(all_baseline_labels.size, dtype=bool)
    frame_times = np.arange(all_baseline_labels.size) * (
        HOP_LENGTH / held_out_audio.sample_rate
    )
    for annotation in annotations:
        if annotation.song_id == split.held_out_song_id:
            annotation_mask |= (frame_times >= annotation.start_seconds) & (
                frame_times < annotation.end_seconds
            )
    model_predictions = all_model_predictions[annotation_mask]
    baseline_predictions = all_baseline_labels[annotation_mask]
    if baseline_predictions.size != held_out_labels.size:
        raise ValueError("Baseline and trained model did not score the same frames.")

    model_metrics = _score(held_out_labels, model_predictions)
    baseline_metrics = _score(held_out_labels, baseline_predictions)
    train_label_set = set(training_labels.tolist())
    held_out_label_counts = {
        label: int(np.count_nonzero(held_out_labels == label))
        for label in sorted(set(held_out_labels.tolist()))
    }
    unsupported = tuple(
        (label, count)
        for label, count in held_out_label_counts.items()
        if label not in train_label_set
    )
    augmented_songs = {
        annotation.song_id
        for annotation in annotations
        if annotation.chord_label.endswith("aug")
    }
    model_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=f".{model_path.name}.",
            suffix=".tmp",
            dir=model_path.parent,
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
        joblib.dump(
            {
                "model": model,
                "labels": tuple(str(label) for label in model.classes_),
                "feature_names": tuple(f"chroma_{index}" for index in range(12)),
                "version": 1,
            },
            temporary_path,
        )
        os.replace(temporary_path, model_path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)

    return TrainingReport(
        model_path=model_path,
        split=split,
        training_labels=tuple(sorted(train_label_set)),
        held_out_labels=tuple(sorted(held_out_label_counts)),
        unsupported_labels=unsupported,
        model_metrics=model_metrics,
        baseline_metrics=baseline_metrics,
        augmented_song_count=len(augmented_songs),
        feedback_song_ids=tuple(sorted(feedback_song_ids)),
    )


def format_report(report: TrainingReport) -> str:
    lines = [
        "Chord model training complete.",
        f"Training songs: {', '.join(report.split.training_song_ids)}",
        f"Held-out song: {report.split.held_out_song_id}",
        f"Held-out labeled frames: {report.model_metrics.frame_count}",
    ]
    if report.feedback_song_ids:
        lines.append(
            "Reviewed feedback included in training: "
            + ", ".join(report.feedback_song_ids)
        )
    if report.unsupported_labels:
        unsupported = ", ".join(
            f"{label} ({count} frames)" for label, count in report.unsupported_labels
        )
        lines.append(f"Labels absent from training (counted as misses): {unsupported}")
    if report.augmented_song_count:
        lines.append(
            "Augmented-label limitation: Daug/Eaug are represented by "
            f"{report.augmented_song_count} training song(s); cross-song "
            "performance is not independently measured."
        )
    lines.extend(
        [
            (
                "Trained model: "
                f"accuracy {report.model_metrics.accuracy:.3f}, "
                f"macro-F1 {report.model_metrics.macro_f1:.3f}"
            ),
            (
                "Template baseline: "
                f"accuracy {report.baseline_metrics.accuracy:.3f}, "
                f"macro-F1 {report.baseline_metrics.macro_f1:.3f}"
            ),
            f"Saved model: {report.model_path}",
            "This held-out result measures only this song and does not establish "
            "accuracy on unfamiliar music.",
        ]
    )
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Train a local chord classifier and compare it on a held-out song."
    )
    parser.add_argument(
        "--annotations",
        type=Path,
        default=DEFAULT_ROOT / "data" / "training" / "annotations.csv",
    )
    parser.add_argument(
        "--split",
        type=Path,
        default=DEFAULT_ROOT / "data" / "training" / "split.json",
    )
    parser.add_argument(
        "--model",
        type=Path,
        default=DEFAULT_ROOT / "models" / "chord_classifier.joblib",
    )
    parser.add_argument(
        "--include-reviewed-feedback",
        action="store_true",
        help=(
            "include locally saved feedback after its song IDs are reviewed and "
            "assigned to training_song_ids in the split file"
        ),
    )
    args = parser.parse_args(argv)

    try:
        feedback_paths = (
            feedback_annotation_paths(DEFAULT_ROOT)
            if args.include_reviewed_feedback
            else ()
        )
        if args.include_reviewed_feedback and not feedback_paths:
            raise ValueError(
                "No saved feedback manifests were found under "
                "output/training-feedback/."
            )
        report = train_and_evaluate(
            args.annotations,
            args.split,
            args.model,
            root=DEFAULT_ROOT,
            feedback_paths=feedback_paths,
        )
    except (OSError, ValueError) as exc:
        print(f"Training failed: {exc}", file=sys.stderr)
        return 2

    print(format_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
