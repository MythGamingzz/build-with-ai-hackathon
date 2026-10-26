from html import escape
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import (
    Flowable,
    LayoutError,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

from cadence.chart_data import ChartBar, ChartData, ChartGroup, bar_beat_slots

_MATCH_FILL = colors.HexColor("#f5dfad")


class _MeasureRow(Flowable):
    def __init__(self, bars: tuple[ChartBar, ...], beats_per_bar: int) -> None:
        super().__init__()
        self.bars = bars
        self.beats_per_bar = beats_per_bar
        self.height = 36

    def wrap(
        self,
        available_width: float,
        available_height: float,
    ) -> tuple[float, float]:
        self.width = available_width
        return self.width, self.height

    def draw(self) -> None:
        canvas = self.canv
        measure_width = self.width / len(self.bars)
        for bar_index, bar in enumerate(self.bars):
            x = bar_index * measure_width
            canvas.setFillColor(colors.HexColor("#8b642e"))
            canvas.setFont("Helvetica", 7)
            canvas.drawString(x + 2, 25, f"Bar {bar.number}")
            canvas.setFillColor(colors.black)
            canvas.setStrokeColor(colors.HexColor("#bd8640"))
            canvas.setLineWidth(1.5)
            canvas.line(x + 3, 4, x + 3, 21)
            canvas.line(x + measure_width - 3, 4, x + measure_width - 3, 21)

            slot_left = x + 12
            slot_width = (measure_width - 24) / self.beats_per_bar
            for slot_index, slot in enumerate(
                bar_beat_slots(
                    bar,
                    self.beats_per_bar,
                    include_no_chord=True,
                )
            ):
                unique_labels: dict[str, tuple[bool, bool]] = {}
                for chord in slot:
                    if chord.label == "N":
                        continue
                    previous = unique_labels.get(chord.label, (False, False))
                    unique_labels[chord.label] = (
                        previous[0] or chord.highlighted,
                        previous[1] or chord.is_user_corrected,
                    )
                if unique_labels:
                    label = "/".join(
                        f"{chord_label}{'*' if corrected else ''}"
                        for chord_label, (_, corrected) in unique_labels.items()
                    )
                else:
                    corrected_no_chord = any(
                        chord.label == "N" and chord.is_user_corrected
                        for chord in slot
                    )
                    label = ".*" if corrected_no_chord else "."
                highlighted = any(
                    highlight for highlight, _ in unique_labels.values()
                )
                font_size = 8.0
                label_width = stringWidth(label, "Courier", font_size)
                while label_width > slot_width - 2 and font_size > 5.5:
                    font_size -= 0.5
                    label_width = stringWidth(label, "Courier", font_size)
                label_x = slot_left + slot_index * slot_width
                center_x = label_x + slot_width / 2
                if highlighted:
                    canvas.setFillColor(_MATCH_FILL)
                    canvas.roundRect(
                        center_x - label_width / 2 - 2,
                        5,
                        label_width + 4,
                        13,
                        2,
                        stroke=0,
                        fill=1,
                    )
                canvas.setFillColor(colors.black)
                canvas.setFont("Courier", font_size)
                canvas.drawCentredString(center_x, 8, label)


def create_chart_pdf(data: ChartData) -> bytes:
    buffer = BytesIO()
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ChartTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#302c25"),
    )
    section_style = ParagraphStyle(
        "ChartSection",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#302c25"),
        spaceBefore=10,
        spaceAfter=5,
    )
    body_style = ParagraphStyle(
        "ChartBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
    )
    cell_style = ParagraphStyle(
        "ChartMetadata",
        parent=body_style,
        alignment=TA_CENTER,
    )
    document = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=0.4 * inch,
        leftMargin=0.4 * inch,
        topMargin=0.4 * inch,
        bottomMargin=0.4 * inch,
        title=data.title,
        author="Cadence",
        pageCompression=0,
    )
    story = [
        Paragraph(escape(data.title), title_style),
        Spacer(1, 8),
        Paragraph(
            f"Key: {escape(data.key)} &nbsp;&nbsp; "
            f"Tempo: {data.tempo_bpm:g} BPM &nbsp;&nbsp; "
            f"Time signature: {escape(data.time_signature)}",
            cell_style,
        ),
        Paragraph(
            "Chord placements are experimental estimates, not verified sheet music. "
            "Confirm all chords and timing before performance.",
            cell_style,
        ),
        Paragraph(
            (
                "No chord was predicted; empty beats are shown as dots and the full "
                "recording duration is retained."
                if data.chart_start_seconds is None
                else (
                    (
                        f"Bar 1 stays anchored at the original chart start "
                        f"({data.chart_start_seconds:.2f}s); any earlier no-chord "
                        "intro is excluded."
                    )
                    if data.chart_start_is_fixed
                    else (
                        f"Bar 1 starts at the first predicted chord "
                        f"({data.chart_start_seconds:.2f}s); any earlier no-chord "
                        "intro is excluded."
                    )
                )
            ),
            cell_style,
        ),
        Spacer(1, 8),
    ]
    if any(
        chord.is_user_corrected
        for group in data.groups
        for bar in group.bars
        for chord in bar.chords
    ):
        story.insert(
            4,
            Paragraph(
                "* marks a user-corrected chord label; unmarked labels are model estimates.",
                cell_style,
            ),
        )
    for group in data.groups:
        story.append(Paragraph(escape(group.name), section_style))
        if group.match is not None and group.match.progression is not None:
            progression = group.match.progression
            story.append(
                Paragraph(
                    "Possible progression: "
                    f"{escape(progression.name)} in {escape(group.match.key or '')} "
                    "(heuristic match; highlighted chords are suggestions).",
                    body_style,
                )
            )
            story.append(Spacer(1, 4))
        for row_start in range(0, len(group.bars), 4):
            story.append(
                _MeasureRow(
                    group.bars[row_start : row_start + 4],
                    data.beats_per_bar,
                )
            )
            story.append(Spacer(1, 4))
        story.append(Spacer(1, 5))
    try:
        document.build(story)
    except (LayoutError, OSError, TypeError, UnicodeEncodeError, ValueError) as exc:
        raise RuntimeError(f"Could not create the performance chart PDF: {exc}") from exc
    return buffer.getvalue()
