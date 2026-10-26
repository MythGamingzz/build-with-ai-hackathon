from html import escape
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from cadence.chart_data import ChartBar, ChartData, ChartGroup

_MATCH_FILL = colors.HexColor("#f5dfad")
_HEADER_FILL = colors.HexColor("#e9e2d5")


def _beat_cell(bar: ChartBar, beat_slot: int) -> tuple[str, bool]:
    chords = [
        chord
        for chord in bar.chords
        if int(chord.beat) == beat_slot
    ]
    lines = [
        f"{chord.beat:g}: {escape(chord.label)}"
        for chord in chords
    ]
    return "<br/>".join(lines), any(chord.highlighted for chord in chords)


def _group_table(
    data: ChartData,
    group: ChartGroup,
    cell_style: ParagraphStyle,
) -> Table:
    headers = ["Bar"] + [f"Beat {beat}" for beat in range(1, data.beats_per_bar + 1)]
    rows = [[Paragraph(header, cell_style) for header in headers]]
    highlighted_cells: list[tuple[int, int]] = []
    for row_index, bar in enumerate(group.bars, start=1):
        row = [Paragraph(str(bar.number), cell_style)]
        for beat_slot in range(1, data.beats_per_bar + 1):
            text, highlighted = _beat_cell(bar, beat_slot)
            row.append(Paragraph(text, cell_style))
            if highlighted:
                highlighted_cells.append((beat_slot, row_index))

        rows.append(row)

    page_width = landscape(letter)[0] - 0.8 * inch
    bar_width = 0.5 * inch
    beat_width = (page_width - bar_width) / data.beats_per_bar
    table = Table(
        rows,
        colWidths=[bar_width] + [beat_width] * data.beats_per_bar,
        repeatRows=1,
        hAlign="LEFT",
    )
    commands = [
        ("BACKGROUND", (0, 0), (-1, 0), _HEADER_FILL),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#756d60")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]
    commands.extend(
        ("BACKGROUND", (column, row), (column, row), _MATCH_FILL)
        for column, row in highlighted_cells
    )
    table.setStyle(TableStyle(commands))
    return table


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
        "ChartCell",
        parent=body_style,
        fontSize=8,
        leading=10,
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
            body_style,
        ),
        Paragraph(
            "Chord placements are experimental estimates, not verified sheet music. "
            "Confirm all chords and timing before performance.",
            body_style,
        ),
        Spacer(1, 8),
    ]
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
        story.append(_group_table(data, group, cell_style))
        story.append(Spacer(1, 8))
    try:
        document.build(story)
    except (OSError, TypeError, UnicodeEncodeError, ValueError) as exc:
        raise RuntimeError(f"Could not create the performance chart PDF: {exc}") from exc
    return buffer.getvalue()
