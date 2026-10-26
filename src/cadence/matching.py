import re
from dataclasses import dataclass
from typing import Sequence

from cadence.progression_data import Progression
from cadence.theory import MAJOR_KEYS, note_pitch_class, spell_progression

_CHORD_LABEL = re.compile(r"^([A-G][#b]?)(m|aug)?$")


@dataclass(frozen=True)
class ProgressionCandidate:
    progression: Progression
    key: str
    matched_event_indices: tuple[int, ...]


@dataclass(frozen=True)
class ProgressionMatch:
    progression: Progression | None
    key: str | None
    ambiguous: bool
    candidate_names: tuple[str, ...]
    matched_event_indices: tuple[int, ...] = ()
    candidates: tuple[ProgressionCandidate, ...] = ()


def _chord_signature(label: str) -> tuple[int, str] | None:
    if label == "N":
        return None
    match = _CHORD_LABEL.fullmatch(label)
    if match is None:
        raise ValueError(f"Unsupported predicted chord label: {label!r}.")
    root, suffix = match.groups()
    quality = {"": "major", "m": "minor", "aug": "augmented"}[suffix or ""]
    return note_pitch_class(root), quality


def _collapsed_chords(
    chord_labels: Sequence[str],
) -> tuple[tuple[tuple[int, str], tuple[int, ...]], ...]:
    collapsed: list[tuple[tuple[int, str], list[int]]] = []
    for index, label in enumerate(chord_labels):
        signature = _chord_signature(label)
        if signature is None:
            continue
        if collapsed and signature == collapsed[-1][0]:
            collapsed[-1][1].append(index)
        else:
            collapsed.append((signature, [index]))
    return tuple((signature, tuple(indices)) for signature, indices in collapsed)


def match_progression(
    chord_labels: Sequence[str],
    progressions: tuple[Progression, ...],
) -> ProgressionMatch:
    observed = _collapsed_chords(chord_labels)
    if not observed:
        return ProgressionMatch(None, None, False, ())

    key_names_by_pitch = {
        note_pitch_class(key): key for key in MAJOR_KEYS
    }
    matches: dict[tuple[str, int], tuple[Progression, str, set[int]]] = {}
    for progression in progressions:
        for key in MAJOR_KEYS:
            expected_chords = spell_progression(
                progression.degrees,
                key,
                progression.qualities,
            )
            expected = tuple(
                (note_pitch_class(chord.notes[0]), chord.quality)
                for chord in expected_chords
            )
            if len(expected) > len(observed):
                continue
            for start in range(len(observed) - len(expected) + 1):
                if tuple(
                    signature for signature, _ in observed[start : start + len(expected)]
                ) == expected:
                    tonic_pitch = note_pitch_class(key)
                    match_key = (progression.id, tonic_pitch)
                    if match_key not in matches:
                        matches[match_key] = (
                            progression,
                            key_names_by_pitch[tonic_pitch],
                            set(),
                        )
                    matches[match_key][2].update(
                        event_index
                        for _, indices in observed[start : start + len(expected)]
                        for event_index in indices
                    )

    if not matches:
        return ProgressionMatch(None, None, False, ())
    if len(matches) > 1:
        candidates = tuple(
            ProgressionCandidate(
                progression=progression,
                key=key,
                matched_event_indices=tuple(sorted(matched_event_indices)),
            )
            for progression, key, matched_event_indices in sorted(
                matches.values(),
                key=lambda item: (item[0].id, item[1]),
            )
        )
        candidate_names = tuple(
            sorted({progression.name for progression, _, _ in matches.values()})
        )
        return ProgressionMatch(
            None,
            None,
            True,
            candidate_names,
            candidates=candidates,
        )

    progression, key, matched_event_indices = next(iter(matches.values()))
    candidate = ProgressionCandidate(
        progression=progression,
        key=key,
        matched_event_indices=tuple(sorted(matched_event_indices)),
    )
    return ProgressionMatch(
        progression,
        key,
        False,
        (progression.name,),
        candidate.matched_event_indices,
        (candidate,),
    )
