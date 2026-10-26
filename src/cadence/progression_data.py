import json
import re
from dataclasses import dataclass
from pathlib import Path

from cadence.theory import SUPPORTED_TRIAD_QUALITIES, roman_numeral_for

FREQUENCY_GROUPS = ("frequent", "medium", "less common")
DEFAULT_PROGRESSIONS_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "progressions.json"
)


@dataclass(frozen=True)
class Progression:
    id: str
    name: str
    roman_numerals: tuple[str, ...]
    degrees: tuple[int, ...]
    qualities: tuple[str, ...]
    frequency: str
    description: str
    theory_relationship: str
    diagram: str | None

    @property
    def pattern(self) -> str:
        return "-".join(self.roman_numerals)


def load_progressions(path: Path = DEFAULT_PROGRESSIONS_PATH) -> tuple[Progression, ...]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read progression catalog {path}: {exc}") from exc
    if not isinstance(raw, list) or not raw:
        raise ValueError(f"Progression catalog must be a non-empty list: {path}")

    entries: list[Progression] = []
    seen_ids: set[str] = set()
    for index, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Progression {index} must be an object.")
        identifier = item.get("id")
        name = item.get("name")
        roman_value = item.get("roman_numerals")
        degrees_value = item.get("degrees")
        qualities_value = item.get("qualities")
        frequency = item.get("frequency")
        description = item.get("description")
        theory_relationship = item.get("theory_relationship")
        diagram = item.get("diagram")

        if not isinstance(identifier, str) or not identifier.strip():
            raise ValueError(f"Progression {index} needs a non-empty id.")
        if identifier in seen_ids:
            raise ValueError(f"Duplicate progression id: {identifier}")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"Progression {identifier} needs a non-empty name.")
        if (
            not isinstance(roman_value, list)
            or not roman_value
            or any(not isinstance(roman, str) for roman in roman_value)
        ):
            raise ValueError(
                f"Progression {identifier} needs a non-empty roman_numerals list."
            )
        if (
            not isinstance(degrees_value, list)
            or not degrees_value
            or any(
                not isinstance(degree, int)
                or isinstance(degree, bool)
                or not 1 <= degree <= 7
                for degree in degrees_value
            )
        ):
            raise ValueError(
                f"Progression {identifier} degrees must be integers from 1 through 7."
            )
        degrees = tuple(degrees_value)
        roman_numerals = tuple(roman_value)
        if (
            not isinstance(qualities_value, list)
            or not qualities_value
            or any(not isinstance(quality, str) for quality in qualities_value)
        ):
            raise ValueError(
                f"Progression {identifier} needs a non-empty qualities list."
            )
        qualities = tuple(qualities_value)
        if len(degrees) != len(roman_numerals) or len(degrees) != len(qualities):
            raise ValueError(
                f"Progression {identifier} must have one Roman numeral and quality "
                "per degree."
            )
        if any(quality not in SUPPORTED_TRIAD_QUALITIES for quality in qualities):
            raise ValueError(
                f"Progression {identifier} qualities must be one of "
                f"{', '.join(SUPPORTED_TRIAD_QUALITIES)}."
            )
        expected_roman = tuple(
            roman_numeral_for(degree, quality)
            for degree, quality in zip(degrees, qualities, strict=True)
        )
        if roman_numerals != expected_roman:
            raise ValueError(
                f"Progression {identifier} Roman numerals do not match its "
                "degrees and qualities."
            )
        if frequency not in FREQUENCY_GROUPS:
            raise ValueError(
                f"Progression {identifier} has unsupported frequency group "
                f"{frequency!r}."
            )
        if not isinstance(description, str) or not description.strip():
            raise ValueError(f"Progression {identifier} needs a description.")
        if not isinstance(theory_relationship, str) or not theory_relationship.strip():
            raise ValueError(f"Progression {identifier} needs a theory relationship.")
        if diagram is not None and not isinstance(diagram, str):
            raise ValueError(f"Progression {identifier} diagram must be a string.")

        entries.append(
            Progression(
                id=identifier,
                name=name,
                roman_numerals=roman_numerals,
                degrees=degrees,
                qualities=qualities,
                frequency=frequency,
                description=description,
                theory_relationship=theory_relationship,
                diagram=diagram,
            )
        )
        seen_ids.add(identifier)

    return tuple(entries)


def search_progressions(
    progressions: tuple[Progression, ...],
    query: str = "",
    frequency: str | None = None,
) -> tuple[Progression, ...]:
    if frequency is not None and frequency not in FREQUENCY_GROUPS:
        raise ValueError(f"Unsupported frequency group: {frequency!r}")

    needle = _normalize_search(query)
    roman_query = tuple(token for token in re.split(r"[\s-]+", needle) if token)
    matches = []
    for progression in progressions:
        if frequency is not None and progression.frequency != frequency:
            continue
        pattern_tokens = tuple(
            roman.casefold() for roman in progression.roman_numerals
        )
        pattern_matches = (
            pattern_tokens == roman_query
            if len(roman_query) > 1
            else bool(roman_query and roman_query[0] in pattern_tokens)
        )
        if not needle or needle in _normalize_search(progression.name) or pattern_matches:
            matches.append(progression)
    return tuple(
        sorted(matches, key=lambda progression: FREQUENCY_GROUPS.index(progression.frequency))
    )


def _normalize_search(value: str) -> str:
    return re.sub(r"\s+", " ", value.casefold().replace("–", "-")).strip()
