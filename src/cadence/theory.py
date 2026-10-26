import re
from dataclasses import dataclass
from typing import Sequence

MAJOR_KEYS = ("C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B")
ROMAN_NUMERALS = ("I", "ii", "iii", "IV", "V", "vi", "vii°")
TRIAD_QUALITIES = (
    "major",
    "minor",
    "minor",
    "major",
    "major",
    "minor",
    "diminished",
)
_MAJOR_SCALES = {
    "C": ("C", "D", "E", "F", "G", "A", "B"),
    "Db": ("Db", "Eb", "F", "Gb", "Ab", "Bb", "C"),
    "D": ("D", "E", "F#", "G", "A", "B", "C#"),
    "Eb": ("Eb", "F", "G", "Ab", "Bb", "C", "D"),
    "E": ("E", "F#", "G#", "A", "B", "C#", "D#"),
    "F": ("F", "G", "A", "Bb", "C", "D", "E"),
    "Gb": ("Gb", "Ab", "Bb", "Cb", "Db", "Eb", "F"),
    "G": ("G", "A", "B", "C", "D", "E", "F#"),
    "Ab": ("Ab", "Bb", "C", "Db", "Eb", "F", "G"),
    "A": ("A", "B", "C#", "D", "E", "F#", "G#"),
    "Bb": ("Bb", "C", "D", "Eb", "F", "G", "A"),
    "B": ("B", "C#", "D#", "E", "F#", "G#", "A#"),
}
_QUALITY_SUFFIXES = {"major": "", "minor": "m", "diminished": "°"}
SUPPORTED_TRIAD_QUALITIES = ("major", "minor", "diminished")
_QUALITY_INTERVALS = {
    "major": (0, 4, 7),
    "minor": (0, 3, 7),
    "diminished": (0, 3, 6),
}
_NATURAL_PITCH_CLASSES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
_ROMAN_NUMERALS_BY_QUALITY = {
    degree: {
        "major": numeral,
        "minor": numeral.lower(),
        "diminished": f"{numeral.lower()}°",
    }
    for degree, numeral in enumerate(("I", "II", "III", "IV", "V", "VI", "VII"), 1)
}


@dataclass(frozen=True)
class TriadChord:
    degree: int
    roman_numeral: str
    quality: str
    symbol: str
    notes: tuple[str, str, str]


def major_scale(key: str) -> tuple[str, ...]:
    try:
        return _MAJOR_SCALES[key]
    except KeyError as exc:
        raise ValueError(
            f"Unsupported major key {key!r}; choose one of {', '.join(MAJOR_KEYS)}."
        ) from exc


def diatonic_chords(key: str) -> tuple[TriadChord, ...]:
    scale = major_scale(key)
    chords = []
    for index, (roman_numeral, quality) in enumerate(
        zip(ROMAN_NUMERALS, TRIAD_QUALITIES, strict=True)
    ):
        notes = tuple(scale[(index + offset) % 7] for offset in (0, 2, 4))
        root = notes[0]
        chords.append(
            TriadChord(
                degree=index + 1,
                roman_numeral=roman_numeral,
                quality=quality,
                symbol=f"{root}{_QUALITY_SUFFIXES[quality]}",
                notes=notes,
            )
        )
    return tuple(chords)


def roman_numeral_for(degree: int, quality: str) -> str:
    if not isinstance(degree, int) or isinstance(degree, bool) or not 1 <= degree <= 7:
        raise ValueError("Progression degrees must be integers from 1 through 7.")
    try:
        return _ROMAN_NUMERALS_BY_QUALITY[degree][quality]
    except KeyError as exc:
        raise ValueError(
            f"Unsupported triad quality {quality!r}; choose from "
            f"{', '.join(SUPPORTED_TRIAD_QUALITIES)}."
        ) from exc


def note_pitch_class(note: str) -> int:
    match = re.fullmatch(r"([A-G])([#b]*)", note)
    if match is None:
        raise ValueError(f"Unsupported note spelling: {note!r}.")
    letter, accidentals = match.groups()
    adjustment = accidentals.count("#") - accidentals.count("b")
    return (_NATURAL_PITCH_CLASSES[letter] + adjustment) % 12


def _spell_note(letter: str, pitch_class: int) -> str:
    natural_pitch = _NATURAL_PITCH_CLASSES[letter]
    for adjustment in (-2, -1, 0, 1, 2):
        if (natural_pitch + adjustment) % 12 == pitch_class % 12:
            suffix = "bb" if adjustment == -2 else "b" if adjustment == -1 else (
                "##" if adjustment == 2 else "#" if adjustment == 1 else ""
            )
            return f"{letter}{suffix}"
    raise ValueError(f"Could not spell pitch class {pitch_class} on {letter}.")


def spell_progression(
    degrees: Sequence[int],
    key: str,
    qualities: Sequence[str] | None = None,
) -> tuple[TriadChord, ...]:
    scale_chords = diatonic_chords(key)
    if not degrees:
        raise ValueError("A progression must contain at least one degree.")
    if any(
        not isinstance(degree, int) or isinstance(degree, bool) or not 1 <= degree <= 7
        for degree in degrees
    ):
        raise ValueError("Progression degrees must be integers from 1 through 7.")
    if qualities is None:
        diatonic_qualities = tuple(chord.quality for chord in scale_chords)
        qualities = tuple(diatonic_qualities[degree - 1] for degree in degrees)
    elif len(qualities) != len(degrees):
        raise ValueError("Progression must have one quality per degree.")

    chords = []
    for degree, quality in zip(degrees, qualities, strict=True):
        if quality not in SUPPORTED_TRIAD_QUALITIES:
            raise ValueError(
                f"Unsupported triad quality {quality!r}; choose from "
                f"{', '.join(SUPPORTED_TRIAD_QUALITIES)}."
            )
        base_notes = scale_chords[degree - 1].notes
        root_pitch = note_pitch_class(base_notes[0])
        notes = tuple(
            _spell_note(base_notes[index][0], root_pitch + interval)
            for index, interval in enumerate(_QUALITY_INTERVALS[quality])
        )
        chords.append(
            TriadChord(
                degree=degree,
                roman_numeral=roman_numeral_for(degree, quality),
                quality=quality,
                symbol=f"{notes[0]}{_QUALITY_SUFFIXES[quality]}",
                notes=notes,
            )
        )
    return tuple(chords)
