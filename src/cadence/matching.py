import re
from dataclasses import dataclass
from typing import Sequence

from cadence.progression_data import Progression
from cadence.theory import MAJOR_KEYS, note_pitch_class, spell_progression

_CHORD_LABEL = re.compile(r"^([A-G][#b]?)(m|aug)?$")


@dataclass(frozen=True)
class ProgressionMatch:
    progression: Progression | None
    key: str | None
    ambiguous: bool
    candidate_names: tuple[str, ...]


def _chord_signature(label: str) -> tuple[int, str] | None:
    if label == "N":
        return None
    match = _CHORD_LABEL.fullmatch(label)
    if match is None:
        raise ValueError(f"Unsupported predicted chord label: {label!r}.")
    root, suffix = match.groups()
    quality = {"": "major", "m": "minor", "aug": "augmented"}[suffix or ""]
    return note_pitch_class(root), quality


def _collapsed_chords(chord_labels: Sequence[str]) -> tuple[tuple[int, str], ...]:
    collapsed: list[tuple[int, str]] = []
    for label in chord_labels:
        signature = _chord_signature(label)
        if signature is not None and (not collapsed or signature != collapsed[-1]):
            collapsed.append(signature)
    return tuple(collapsed)


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
    matches: dict[tuple[str, int], tuple[Progression, str]] = {}
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
                if observed[start : start + len(expected)] == expected:
                    tonic_pitch = note_pitch_class(key)
                    matches[(progression.id, tonic_pitch)] = (
                        progression,
                        key_names_by_pitch[tonic_pitch],
                    )

    if not matches:
        return ProgressionMatch(None, None, False, ())
    if len(matches) > 1:
        candidate_names = tuple(
            sorted({progression.name for progression, _ in matches.values()})
        )
        return ProgressionMatch(None, None, True, candidate_names)

    progression, key = next(iter(matches.values()))
    return ProgressionMatch(progression, key, False, (progression.name,))
