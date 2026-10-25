from dataclasses import dataclass
from html import escape
import json
import math
from pathlib import Path
import string
from typing import Any, Mapping


@dataclass(frozen=True)
class Annotation:
    start: float
    end: float
    label: str


@dataclass(frozen=True)
class Reference:
    recording: str
    lyrics: list[Annotation]
    chords: list[Annotation]


def load_reference(path: Path, recording_name: str, duration: float) -> Reference:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"Reference JSON is invalid: {error}") from error

    if not isinstance(data, dict):
        raise ValueError("Reference JSON must contain an object.")
    if data.get("recording") != recording_name:
        raise ValueError(
            f"Reference recording must be named {recording_name!r}."
        )
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("Recording duration must be a positive finite number.")

    return Reference(
        recording=recording_name,
        lyrics=_read_annotations(data, "lyrics", "text", duration),
        chords=_read_annotations(data, "chords", "label", duration),
    )


def _read_annotations(
    data: dict[str, Any], field: str, label_field: str, duration: float
) -> list[Annotation]:
    entries = data.get(field)
    if not isinstance(entries, list):
        raise ValueError(f"Reference field {field!r} must be a list.")

    annotations: list[Annotation] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ValueError(f"Reference {field}[{index}] must be an object.")
        start = entry.get("start")
        end = entry.get("end")
        label = entry.get(label_field)
        if (
            not isinstance(start, (int, float))
            or isinstance(start, bool)
            or not math.isfinite(start)
            or not isinstance(end, (int, float))
            or isinstance(end, bool)
            or not math.isfinite(end)
        ):
            raise ValueError(
                f"Reference {field}[{index}] needs finite numeric start and end times."
            )
        if start < 0 or end <= start or end > duration:
            raise ValueError(
                f"Reference {field}[{index}] must fit within the recording duration."
            )
        if not isinstance(label, str) or not label.strip():
            raise ValueError(f"Reference {field}[{index}] needs a nonempty {label_field}.")
        annotations.append(Annotation(float(start), float(end), label.strip()))

    return annotations


def _normalized_label(label: str) -> str:
    return " ".join(label.casefold().split()).strip(string.punctuation + "…")


def compare_annotations(
    analysis: Mapping[str, Any], reference: Reference
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    summary: dict[str, dict[str, int | float | None]] = {}

    for kind, label_field, annotations in (
        ("lyrics", "text", reference.lyrics),
        ("chords", "label", reference.chords),
    ):
        predictions = analysis.get(kind, [])
        matched = 0
        correct_seconds = 0.0
        reference_seconds = 0.0

        for annotation in annotations:
            duration = annotation.end - annotation.start
            overlapping: list[tuple[Mapping[str, Any], float]] = []
            for prediction in predictions:
                overlap = max(
                    0.0,
                    min(annotation.end, float(prediction["end"]))
                    - max(annotation.start, float(prediction["start"])),
                )
                if overlap > 0:
                    overlapping.append((prediction, overlap))

            if kind == "lyrics":
                best = max(overlapping, key=lambda item: item[1], default=None)
                predicted_labels = (
                    [str(best[0].get(label_field, ""))] if best is not None else []
                )
                covered = best[1] if best is not None else 0.0
                correct = (
                    covered
                    if best is not None
                    and _normalized_label(str(best[0].get(label_field, "")))
                    == _normalized_label(annotation.label)
                    else 0.0
                )
            else:
                predicted_labels = []
                correct = 0.0
                covered = 0.0
                for prediction, overlap in overlapping:
                    label = str(prediction.get(label_field, ""))
                    if not predicted_labels or predicted_labels[-1] != label:
                        predicted_labels.append(label)
                    covered += overlap
                    if _normalized_label(label) == _normalized_label(annotation.label):
                        correct += overlap
                covered = min(covered, duration)
                correct = min(correct, duration)

            is_match = (
                covered >= duration * 0.8 and correct >= duration * 0.8
            )
            matched += int(is_match)
            correct_seconds += correct
            reference_seconds += duration
            rows.append(
                {
                    "kind": kind,
                    "start": annotation.start,
                    "end": annotation.end,
                    "reference": annotation.label,
                    "prediction": ", ".join(predicted_labels) or "No overlapping estimate",
                    "accuracy": correct / duration,
                    "status": "Match" if is_match else "Mismatch",
                }
            )

        summary[kind] = {
            "evaluated": len(annotations),
            "matched": matched,
            "accuracy": correct_seconds / reference_seconds
            if reference_seconds
            else None,
        }

    return {"rows": rows, "summary": summary}


def build_report_html(
    analysis: Mapping[str, Any],
    reference: Reference,
    comparison: Mapping[str, Any],
) -> str:
    duration = float(analysis["duration_seconds"])
    events: list[dict[str, Any]] = []

    for kind, label_field, lane in (
        ("lyrics", "text", "Sung words"),
        ("chords", "label", "Chords"),
    ):
        for prediction in analysis.get(kind, []):
            events.append(
                {
                    "start": float(prediction["start"]),
                    "end": float(prediction["end"]),
                    "lane": lane,
                    "source": "Estimate",
                    "label": str(prediction.get(label_field, "")),
                    "status": "",
                }
            )

    comparison_rows = comparison["rows"]
    row_by_reference = {
        (row["kind"], row["start"], row["end"], row["reference"]): row
        for row in comparison_rows
    }
    for kind, annotations, lane in (
        ("lyrics", reference.lyrics, "Sung words"),
        ("chords", reference.chords, "Chords"),
    ):
        for annotation in annotations:
            row = row_by_reference[
                (kind, annotation.start, annotation.end, annotation.label)
            ]
            events.append(
                {
                    "start": annotation.start,
                    "end": annotation.end,
                    "lane": lane,
                    "source": "Reference",
                    "label": annotation.label,
                    "status": row["status"],
                }
            )

    events.sort(key=lambda event: (event["start"], event["end"], event["source"]))
    event_rows = "\n".join(
        "<tr>"
        f"<td>{event['start']:.2f}–{event['end']:.2f}</td>"
        f"<td>{escape(event['lane'])}</td>"
        f"<td>{escape(event['source'])}</td>"
        f"<td>{escape(event['label'])}</td>"
        f"<td>{escape(event['status'])}</td>"
        "</tr>"
        for event in events
    )
    comparison_table_rows = "\n".join(
        "<tr>"
        f"<td>{escape(row['kind'])}</td>"
        f"<td>{row['start']:.2f}–{row['end']:.2f}</td>"
        f"<td>{escape(row['reference'])}</td>"
        f"<td>{escape(row['prediction'])}</td>"
        f"<td>{row['accuracy'] * 100:.1f}%</td>"
        f"<td class=\"{row['status'].lower()}\">{escape(row['status'])}</td>"
        "</tr>"
        for row in comparison_rows
    )
    summary_rows = "\n".join(
        "<li>"
        f"{escape(kind.title())}: {values['matched']} of {values['evaluated']} "
        "annotated spans matched; "
        f"{values['accuracy'] * 100:.1f}% time-weighted accuracy"
        "</li>"
        for kind, values in comparison["summary"].items()
        if values["evaluated"]
    )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Cadence local analysis report</title>
  <style>
    body {{ color: #1f2937; font: 16px/1.5 system-ui, sans-serif; margin: 2rem auto; max-width: 1100px; padding: 0 1rem; }}
    h1, h2 {{ color: #111827; }}
    .notice {{ background: #f3f4f6; border-left: 4px solid #6b7280; padding: .75rem 1rem; }}
    table {{ border-collapse: collapse; margin: 1rem 0 2rem; width: 100%; }}
    th, td {{ border-bottom: 1px solid #d1d5db; padding: .55rem; text-align: left; vertical-align: top; }}
    th {{ background: #f9fafb; }}
    .match {{ color: #166534; font-weight: 700; }}
    .mismatch {{ color: #b91c1c; font-weight: 700; }}
    .scroll {{ overflow-x: auto; }}
  </style>
</head>
<body>
  <h1>Cadence analysis comparison</h1>
  <p>Recording: <strong>{escape(reference.recording)}</strong> · Duration: {duration:.2f} seconds</p>
  <p class="notice">Estimates are the model output; reference values are separate hand-checked annotations.
  Only the annotated windows below are evaluated. Results from one recording do not establish general accuracy.</p>
  <h2>Annotated-window results</h2>
  <ul>{summary_rows}</ul>
  <p>A span counts as a match when at least 80% of its duration has the expected label.
  The percentage column shows the matching share for each individual reference span.</p>
  <div class="scroll">
    <table>
      <thead><tr><th>Type</th><th>Time (s)</th><th>Reference</th><th>Overlapping estimate</th><th>Matching duration</th><th>Result</th></tr></thead>
      <tbody>{comparison_table_rows}</tbody>
    </table>
  </div>
  <h2>Shared timeline events</h2>
  <p>Events are ordered by their start time; estimates and references remain distinct.</p>
  <div class="scroll">
    <table>
      <thead><tr><th>Time (s)</th><th>Track</th><th>Source</th><th>Value</th><th>Reference result</th></tr></thead>
      <tbody>{event_rows}</tbody>
    </table>
  </div>
</body>
</html>
"""
