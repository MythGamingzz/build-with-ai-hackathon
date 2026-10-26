import pickle
import zlib
from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
from numpy.typing import NDArray
from sklearn.linear_model import LogisticRegression

from cadence.audio_features import HOP_LENGTH, AudioFeatures
from cadence.chords import CHORD_LABELS, NOTE_NAMES, postprocess_model_labels

MODEL_VERSION = 1
FEATURE_NAMES = tuple(f"chroma_{index}" for index in range(12))
DEFAULT_MODEL_PATH = (
    Path(__file__).resolve().parents[2] / "models" / "chord_classifier.joblib"
)
TRAINING_COMMAND = ".venv\\Scripts\\python.exe -m cadence.training"
SUPPORTED_MODEL_LABELS = set(CHORD_LABELS) | {
    f"{root}aug" for root in NOTE_NAMES
} | {"N"}


class ChordModelError(RuntimeError):
    pass


@dataclass(frozen=True)
class ChordEvent:
    start_seconds: float
    end_seconds: float
    label: str
    score: float


def load_trained_model(path: Path = DEFAULT_MODEL_PATH) -> LogisticRegression:
    if not path.is_file():
        raise ChordModelError(
            f"The trained chord model is missing at {path}. Run "
            f"`{TRAINING_COMMAND}` to create it."
        )

    try:
        payload = joblib.load(path)
    except (
        AttributeError,
        EOFError,
        ImportError,
        KeyError,
        OSError,
        pickle.UnpicklingError,
        TypeError,
        ValueError,
        zlib.error,
    ) as exc:
        raise ChordModelError(
            f"The saved chord model could not be loaded: {exc}. Run "
            f"`{TRAINING_COMMAND}` to rebuild it."
        ) from exc

    if not isinstance(payload, dict):
        raise ChordModelError(
            f"The saved chord model at {path} has an unsupported format. "
            f"Run `{TRAINING_COMMAND}` to rebuild it."
        )
    model = payload.get("model")
    feature_names = payload.get("feature_names")
    labels = payload.get("labels")
    if (
        payload.get("version") != MODEL_VERSION
        or not isinstance(model, LogisticRegression)
        or feature_names != FEATURE_NAMES
        or not isinstance(labels, tuple)
        or labels != tuple(str(label) for label in model.classes_)
        or not set(labels).issubset(SUPPORTED_MODEL_LABELS)
        or getattr(model, "n_features_in_", None) != len(FEATURE_NAMES)
    ):
        raise ChordModelError(
            f"The saved chord model at {path} is incompatible with this app. "
            f"Run `{TRAINING_COMMAND}` to rebuild it."
        )
    return model


def _normalized_features(chroma: NDArray[np.float32]) -> NDArray[np.float32]:
    norms = np.linalg.norm(chroma, axis=0, keepdims=True)
    return (chroma / np.maximum(norms, np.finfo(np.float32).eps)).T.astype(
        np.float32
    )


def predict_chord_events(
    features: AudioFeatures,
    model: LogisticRegression,
) -> tuple[ChordEvent, ...]:
    if features.chroma.ndim != 2 or features.chroma.shape[0] != 12:
        raise ValueError("Expected a 12-bin chroma matrix for chord prediction.")
    if features.chroma.shape[1] == 0:
        raise ValueError("Cannot predict chords from audio with no feature frames.")
    if features.rms.size != features.chroma.shape[1]:
        raise ValueError("Chroma and RMS features must contain the same frame count.")
    if getattr(model, "n_features_in_", None) != 12:
        raise ValueError("The chord model must accept 12 chroma features.")

    model_features = _normalized_features(features.chroma)
    predictions = np.asarray(model.predict(model_features), dtype="<U16")
    if predictions.size != features.chroma.shape[1]:
        raise ValueError("The chord model returned an unexpected number of labels.")

    probabilities = np.asarray(model.predict_proba(model_features), dtype=np.float32)
    if probabilities.shape != (predictions.size, len(model.classes_)):
        raise ValueError("The chord model returned an unexpected score matrix.")
    labels = postprocess_model_labels(predictions, features)

    boundaries = np.flatnonzero(labels[1:] != labels[:-1]) + 1
    starts = np.concatenate(([0], boundaries))
    ends = np.concatenate((boundaries, [labels.size]))
    frame_seconds = HOP_LENGTH / features.sample_rate
    class_indices = {
        str(label): index for index, label in enumerate(model.classes_)
    }
    events = []
    for start_frame, end_frame in zip(starts, ends, strict=True):
        start_time = min(float(start_frame * frame_seconds), features.duration)
        end_time = min(float(end_frame * frame_seconds), features.duration)
        if end_time <= start_time:
            continue
        label = str(labels[start_frame])
        score = (
            0.0
            if label == "N"
            else float(np.mean(probabilities[start_frame:end_frame, class_indices[label]]))
        )
        events.append(ChordEvent(start_time, end_time, label, score))
    return tuple(events)
