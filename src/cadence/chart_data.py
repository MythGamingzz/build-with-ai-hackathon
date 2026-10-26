import math
from dataclasses import dataclass
from typing import Sequence

from cadence.chord_model import ChordEvent
from cadence.matching import ProgressionMatch, match_progression
from cadence.progression_data import Progression
from cadence.song_metadata import bar_beat_position


class ChartDataError(ValueError):
    pass


@dataclass(frozen=True)
class SectionRange:
    name: str
    start_bar: int
    end_bar: int


@dataclass(frozen=True)
class ChartChord:
    beat: float
    label: str
    score: float
    highlighted: bool


@dataclass(frozen=True)
class ChartBar:
    number: int
    chords: tuple[ChartChord, ...]


@dataclass(frozen=True)
class ChartGroup:
    name: str
    bars: tuple[ChartBar, ...]
    match: ProgressionMatch | None


@dataclass(frozen=True)
class ChartData:
    title: str
    key: str
    tempo_bpm: float
    time_signature: str
    duration: float
    beats_per_bar: int
    groups: tuple[ChartGroup, ...]


def bar_beat_slots(
    bar: ChartBar,
    beats_per_bar: int,
) -> tuple[tuple[ChartChord, ...], ...]:
    if isinstance(beats_per_bar, bool) or not isinstance(beats_per_bar, int):
        raise ValueError("Beats per bar must be a positive whole number.")
    if beats_per_bar < 1:
        raise ValueError("Beats per bar must be a positive whole number.")
    slots: list[list[ChartChord]] = [[] for _ in range(beats_per_bar)]
    for chord in bar.chords:
        slot = min(
            beats_per_bar,
            max(1, math.floor(chord.beat + 0.5)),
        )
        slots[slot - 1].append(chord)
    return tuple(tuple(slot) for slot in slots)


def format_bar_measure(bar: ChartBar, beats_per_bar: int) -> str:
    slots = bar_beat_slots(bar, beats_per_bar)
    labels = [
        "/".join(dict.fromkeys(chord.label for chord in slot)) if slot else "."
        for slot in slots
    ]
    return f"| {' '.join(labels)} |"


def total_bar_count(duration: float, tempo_bpm: float, time_signature: str) -> int:
    if not math.isfinite(duration) or duration <= 0:
        raise ChartDataError("Song duration must be a positive finite number.")
    if not math.isfinite(tempo_bpm) or tempo_bpm <= 0:
        raise ChartDataError("Tempo must be a positive finite number.")
    try:
        numerator_text, denominator_text = time_signature.split("/", maxsplit=1)
        numerator = int(numerator_text)
        denominator = int(denominator_text)
    except (AttributeError, TypeError, ValueError) as exc:
        raise ChartDataError(
            f"Unsupported time signature: {time_signature!r}."
        ) from exc
    if numerator < 1 or denominator not in {2, 4, 8, 16}:
        raise ChartDataError(f"Unsupported time signature: {time_signature!r}.")
    bar_seconds = 60.0 / tempo_bpm * 4.0 / denominator * numerator
    return max(1, math.ceil(duration / bar_seconds))


def _validate_sections(
    sections: Sequence[SectionRange],
    total_bars: int,
) -> tuple[SectionRange, ...]:
    for section in sections:
        if not isinstance(section, SectionRange):
            raise ChartDataError("Each song section must have a name and bar range.")
        if not isinstance(section.name, str):
            raise ChartDataError("Each section needs a text label.")
        if (
            isinstance(section.start_bar, bool)
            or isinstance(section.end_bar, bool)
            or not isinstance(section.start_bar, int)
            or not isinstance(section.end_bar, int)
        ):
            raise ChartDataError("Section start and end bars must be whole numbers.")
    ordered = tuple(sorted(sections, key=lambda section: section.start_bar))
    previous_end = 0
    for section in ordered:
        if (
            section.start_bar < 1
            or section.end_bar < section.start_bar
            or section.end_bar > total_bars
        ):
            raise ChartDataError(
                f"Section {section.name.strip() or '(unnamed)'!r} must use bar "
                f"numbers from 1 through {total_bars}, with its end at or after "
                "its start."
            )
        if section.start_bar <= previous_end:
            raise ChartDataError(
                f"Section {section.name.strip() or '(unnamed)'!r} overlaps an "
                "earlier section. Adjust the section bar ranges before updating."
            )
        previous_end = section.end_bar
    return ordered


def build_chart_data(
    *,
    title: str,
    key: str,
    tempo_bpm: float,
    time_signature: str,
    duration: float,
    events: Sequence[ChordEvent],
    sections: Sequence[SectionRange],
    progressions: tuple[Progression, ...],
    first_beat_time: float = 0.0,
) -> ChartData:
    clean_title = title.strip()
    if not clean_title:
        raise ChartDataError("Enter a song title before updating the chart preview.")
    if not isinstance(key, str) or not key.strip():
        raise ChartDataError("Choose a key before updating the chart preview.")
    if not math.isfinite(first_beat_time):
        raise ChartDataError("The first beat must be a finite time value.")

    bar_count = total_bar_count(duration, tempo_bpm, time_signature)
    try:
        beats_per_bar = int(time_signature.split("/", maxsplit=1)[0])
    except (AttributeError, TypeError, ValueError) as exc:
        raise ChartDataError(f"Unsupported time signature: {time_signature!r}.") from exc
    valid_sections = _validate_sections(sections, bar_count)

    event_positions: dict[int, tuple[int, float]] = {}
    for index, event in enumerate(events):
        if (
            not math.isfinite(event.start_seconds)
            or not math.isfinite(event.end_seconds)
            or event.start_seconds < 0
            or event.end_seconds < event.start_seconds
            or not math.isfinite(event.score)
        ):
            raise ChartDataError(f"Chord event {index + 1} has invalid timing or score.")
        if event.start_seconds >= duration:
            continue
        event_positions[index] = bar_beat_position(
            event.start_seconds,
            tempo_bpm,
            time_signature,
            first_beat_time,
        )

    assigned_bars: dict[int, SectionRange | None] = {
        number: None for number in range(1, bar_count + 1)
    }
    for section in valid_sections:
        for number in range(section.start_bar, section.end_bar + 1):
            assigned_bars[number] = section

    groups: list[ChartGroup] = []
    for section in valid_sections:
        if not section.name.strip():
            continue
        section_event_indices = [
            index
            for index, (bar, _) in event_positions.items()
            if section.start_bar <= bar <= section.end_bar
        ]
        section_match = match_progression(
            [events[index].label for index in section_event_indices],
            progressions,
        )
        highlighted_indices = (
            {
                section_event_indices[index]
                for index in section_match.matched_event_indices
            }
            if section_match.progression is not None
            else set()
        )
        bars = tuple(
            ChartBar(
                number=number,
                chords=tuple(
                    ChartChord(
                        beat=beat,
                        label=events[index].label,
                        score=events[index].score,
                        highlighted=index in highlighted_indices,
                    )
                    for index, (bar, beat) in sorted(
                        event_positions.items(),
                        key=lambda item: (item[1][0], item[1][1]),
                    )
                    if bar == number
                ),
            )
            for number in range(section.start_bar, section.end_bar + 1)
        )
        groups.append(
            ChartGroup(section.name.strip(), bars, section_match)
        )

    unsectioned_bars = tuple(
        ChartBar(
            number=number,
            chords=tuple(
                ChartChord(
                    beat=beat,
                    label=events[index].label,
                    score=events[index].score,
                    highlighted=False,
                )
                for index, (bar, beat) in sorted(
                    event_positions.items(),
                    key=lambda item: (item[1][0], item[1][1]),
                )
                if bar == number
            ),
        )
        for number in range(1, bar_count + 1)
        if assigned_bars[number] is None
        or not assigned_bars[number].name.strip()
    )
    if unsectioned_bars:
        groups.append(ChartGroup("Unsectioned", unsectioned_bars, None))

    return ChartData(
        title=clean_title,
        key=key.strip(),
        tempo_bpm=float(tempo_bpm),
        time_signature=time_signature,
        duration=float(duration),
        beats_per_bar=beats_per_bar,
        groups=tuple(groups),
    )
