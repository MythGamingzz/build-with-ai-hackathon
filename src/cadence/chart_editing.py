from dataclasses import dataclass
import math
from typing import Mapping, Sequence

from cadence.chord_model import ChordEvent, SUPPORTED_MODEL_LABELS
from cadence.chart_data import first_chord_start, total_bar_count
from cadence.song_metadata import bar_beat_position

BeatAddress = tuple[int, int]


class BeatCellEditError(ValueError):
    pass


@dataclass(frozen=True)
class BeatEditResult:
    events: tuple[ChordEvent, ...]
    corrected_event_indices: frozenset[int]
    original_feedback_events: tuple[ChordEvent, ...]
    corrected_feedback_events: tuple[ChordEvent, ...]
    chart_start_seconds: float | None
    changed_cell_count: int


def parse_beat_cell(value: str) -> tuple[str, ...]:
    if not isinstance(value, str) or not value.strip():
        raise BeatCellEditError(
            "Enter a chord label, N, or .; an empty cell is not valid."
        )
    label = value.strip()
    if "/" in label or "," in label:
        raise BeatCellEditError(
            "Enter one supported chord symbol per beat. Slash chords and "
            "multiple labels are not supported; use N or . for no chord."
        )
    if label in {"N", "."}:
        return ("N",)
    if label not in SUPPORTED_MODEL_LABELS:
        raise BeatCellEditError(
            f"Unsupported chord label {label!r}. Use a supported chord "
            "symbol, or N or . for no chord."
        )
    return (label,)


def _format_labels(labels: Sequence[str]) -> str:
    visible = tuple(dict.fromkeys(label for label in labels if label != "N"))
    if visible:
        return ", ".join(visible)
    return "N" if "N" in labels else "."


def _time_signature_parts(time_signature: str) -> tuple[int, int]:
    try:
        numerator_text, denominator_text = time_signature.split("/", maxsplit=1)
        numerator = int(numerator_text)
        denominator = int(denominator_text)
    except (AttributeError, TypeError, ValueError) as exc:
        raise BeatCellEditError(
            f"Unsupported time signature: {time_signature!r}."
        ) from exc
    if numerator < 1 or denominator not in {2, 4, 8, 16}:
        raise BeatCellEditError(
            f"Unsupported time signature: {time_signature!r}."
        )
    return numerator, denominator


def _event_cell(
    event: ChordEvent,
    *,
    tempo_bpm: float,
    time_signature: str,
    chart_start_seconds: float,
    beats_per_bar: int,
) -> BeatAddress:
    bar_number, beat = bar_beat_position(
        event.start_seconds,
        tempo_bpm,
        time_signature,
        chart_start_seconds,
    )
    beat_number = min(beats_per_bar, max(1, math.floor(beat + 0.5)))
    return bar_number, beat_number


def default_beat_cells(
    events: Sequence[ChordEvent],
    *,
    duration: float,
    tempo_bpm: float,
    time_signature: str,
    chart_start_seconds: float | None = None,
) -> dict[BeatAddress, str]:
    if not math.isfinite(duration) or duration <= 0:
        raise BeatCellEditError("Song duration must be a positive finite number.")
    if not math.isfinite(tempo_bpm) or tempo_bpm <= 0:
        raise BeatCellEditError("Tempo must be a positive finite number.")
    numerator, _ = _time_signature_parts(time_signature)
    inferred_start = first_chord_start(events, duration)
    chart_start = (
        inferred_start
        if chart_start_seconds is None
        else chart_start_seconds
    )
    if chart_start is not None and (
        not math.isfinite(chart_start) or chart_start < 0 or chart_start >= duration
    ):
        raise BeatCellEditError(
            "The chart start must be within the recording duration."
        )
    origin = chart_start if chart_start is not None else 0.0
    bar_count = total_bar_count(
        duration - origin,
        tempo_bpm,
        time_signature,
    )
    labels_by_cell: dict[BeatAddress, list[str]] = {}
    for event in events:
        if event.start_seconds < origin or event.start_seconds >= duration:
            continue
        address = _event_cell(
            event,
            tempo_bpm=tempo_bpm,
            time_signature=time_signature,
            chart_start_seconds=origin,
            beats_per_bar=numerator,
        )
        labels_by_cell.setdefault(address, []).append(event.label)

    return {
        (bar_number, beat_number): _format_labels(
            labels_by_cell.get((bar_number, beat_number), ())
        )
        for bar_number in range(1, bar_count + 1)
        for beat_number in range(1, numerator + 1)
    }


def apply_beat_cell_edits(
    events: Sequence[ChordEvent],
    values: Mapping[BeatAddress, str],
    *,
    duration: float,
    tempo_bpm: float,
    time_signature: str,
) -> BeatEditResult:
    inferred_start = first_chord_start(events, duration)
    origin = inferred_start if inferred_start is not None else 0.0
    defaults = default_beat_cells(
        events,
        duration=duration,
        tempo_bpm=tempo_bpm,
        time_signature=time_signature,
        chart_start_seconds=origin,
    )
    numerator, denominator = _time_signature_parts(time_signature)
    seconds_per_beat = 60.0 / tempo_bpm * 4.0 / denominator
    events_by_cell: dict[BeatAddress, list[int]] = {}
    for index, event in enumerate(events):
        if event.start_seconds < origin or event.start_seconds >= duration:
            continue
        address = _event_cell(
            event,
            tempo_bpm=tempo_bpm,
            time_signature=time_signature,
            chart_start_seconds=origin,
            beats_per_bar=numerator,
        )
        events_by_cell.setdefault(address, []).append(index)

    removed_indices: set[int] = set()
    replacements: list[tuple[BeatAddress, tuple[str, ...]]] = []
    original_feedback: list[ChordEvent] = []
    corrected_feedback: list[ChordEvent] = []
    for address, default_value in defaults.items():
        value = values.get(address, default_value)
        if value.strip() == default_value:
            continue
        edited_labels = parse_beat_cell(value)
        try:
            default_labels = parse_beat_cell(default_value)
        except BeatCellEditError:
            default_labels = ()
        if edited_labels == default_labels:
            continue

        removed_indices.update(events_by_cell.get(address, ()))
        replacements.append((address, edited_labels))
        bar_number, beat_number = address
        start = origin + (
            (bar_number - 1) * numerator + beat_number - 1
        ) * seconds_per_beat
        end = min(duration, start + seconds_per_beat)
        original_feedback.append(
            ChordEvent(start, end, default_value, 0.0)
        )
        corrected_feedback.append(
            ChordEvent(start, end, edited_labels[0], 0.0)
        )

    tagged_events = [
        (event, False)
        for index, event in enumerate(events)
        if index not in removed_indices
    ]
    for address, labels in replacements:
        bar_number, beat_number = address
        start = origin + (
            (bar_number - 1) * numerator + beat_number - 1
        ) * seconds_per_beat
        end = min(duration, start + seconds_per_beat)
        for label in labels:
            tagged_events.append((ChordEvent(start, end, label, 0.0), True))

    changed = bool(replacements)
    tagged_events.sort(key=lambda item: item[0].start_seconds)
    corrected_indices = frozenset(
        index
        for index, (_, is_corrected) in enumerate(tagged_events)
        if is_corrected
    )
    return BeatEditResult(
        events=tuple(event for event, _ in tagged_events),
        corrected_event_indices=corrected_indices,
        original_feedback_events=tuple(original_feedback),
        corrected_feedback_events=tuple(corrected_feedback),
        chart_start_seconds=origin if changed else None,
        changed_cell_count=len(replacements),
    )
