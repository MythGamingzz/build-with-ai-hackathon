import csv
import os
import re
import tempfile
import uuid
from pathlib import Path
from typing import Sequence

from cadence.chord_model import ChordEvent, SUPPORTED_MODEL_LABELS

DEFAULT_ROOT = Path(__file__).resolve().parents[2]
FEEDBACK_DIRECTORY = Path("output") / "training-feedback"
ANNOTATION_FIELDS = (
    "song_id",
    "audio_path",
    "start_seconds",
    "end_seconds",
    "chord_label",
)
_FEEDBACK_ID_PATTERN = re.compile(r"^feedback_[0-9a-f]{32}$")


class FeedbackSaveError(ValueError):
    pass


def feedback_annotation_paths(root: Path = DEFAULT_ROOT) -> tuple[Path, ...]:
    feedback_root = root / FEEDBACK_DIRECTORY
    return tuple(
        sorted(feedback_root.glob("feedback_*/annotations.csv"))
    )


def _changed_events(
    original_events: Sequence[ChordEvent],
    corrected_events: Sequence[ChordEvent],
) -> tuple[ChordEvent, ...]:
    if len(original_events) != len(corrected_events):
        raise FeedbackSaveError("Chord edits must keep the original event timings.")
    changed = []
    for index, (original, corrected) in enumerate(
        zip(original_events, corrected_events, strict=True),
        start=1,
    ):
        if (
            original.start_seconds != corrected.start_seconds
            or original.end_seconds != corrected.end_seconds
            or original.score != corrected.score
        ):
            raise FeedbackSaveError(
                f"Chord event {index} has changed timing or score; only labels "
                "can be saved as feedback."
            )
        if corrected.label not in SUPPORTED_MODEL_LABELS:
            raise FeedbackSaveError(
                f"Chord event {index} has an unsupported label: "
                f"{corrected.label!r}."
            )
        if corrected.label != original.label:
            changed.append(corrected)
    if not changed:
        raise FeedbackSaveError(
            "Change at least one chord label before saving training feedback."
        )
    return tuple(changed)


def _write_annotations(
    path: Path,
    *,
    song_id: str,
    audio_path: Path,
    root: Path,
    events: Sequence[ChordEvent],
) -> None:
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            prefix=".annotations-",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            writer = csv.DictWriter(temporary, fieldnames=ANNOTATION_FIELDS)
            writer.writeheader()
            for event in events:
                writer.writerow(
                    {
                        "song_id": song_id,
                        "audio_path": audio_path.relative_to(root).as_posix(),
                        "start_seconds": f"{event.start_seconds:.6f}",
                        "end_seconds": f"{event.end_seconds:.6f}",
                        "chord_label": event.label,
                    }
                )
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def save_feedback_example(
    *,
    audio_bytes: bytes,
    filename: str,
    original_events: Sequence[ChordEvent],
    corrected_events: Sequence[ChordEvent],
    root: Path = DEFAULT_ROOT,
    feedback_id: str | None = None,
) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in {".mp3", ".wav"}:
        raise FeedbackSaveError("Only WAV and MP3 recordings can be saved.")
    if not audio_bytes:
        raise FeedbackSaveError("The selected audio file is empty.")
    changed = _changed_events(original_events, corrected_events)
    saved_id = feedback_id or f"feedback_{uuid.uuid4().hex}"
    if not _FEEDBACK_ID_PATTERN.fullmatch(saved_id):
        raise FeedbackSaveError("The local feedback identifier is invalid.")

    resolved_root = root.resolve()
    feedback_root = (resolved_root / FEEDBACK_DIRECTORY).resolve()
    feedback_root.mkdir(parents=True, exist_ok=True)
    final_directory = feedback_root / saved_id
    audio_path = final_directory / f"audio{suffix}"
    annotations_path = final_directory / "annotations.csv"

    if final_directory.exists():
        if final_directory.is_symlink() or not audio_path.is_file():
            raise FeedbackSaveError(
                "The saved feedback folder is incomplete or has been replaced."
            )
        if audio_path.read_bytes() != audio_bytes:
            raise FeedbackSaveError(
                "The selected recording changed. Analyze it again before saving."
            )
        _write_annotations(
            annotations_path,
            song_id=saved_id,
            audio_path=audio_path,
            root=resolved_root,
            events=changed,
        )
        return saved_id

    with tempfile.TemporaryDirectory(
        prefix=f".{saved_id}-",
        dir=feedback_root,
    ) as temporary_directory:
        temporary_root = Path(temporary_directory)
        temporary_audio = temporary_root / f"audio{suffix}"
        temporary_annotations = temporary_root / "annotations.csv"
        temporary_audio.write_bytes(audio_bytes)
        _write_annotations(
            temporary_annotations,
            song_id=saved_id,
            audio_path=audio_path,
            root=resolved_root,
            events=changed,
        )
        os.replace(temporary_root, final_directory)
    return saved_id
