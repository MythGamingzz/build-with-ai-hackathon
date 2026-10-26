import hashlib
from html import escape
import math
from pathlib import Path
from urllib.parse import quote

import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile

from cadence.audio_examples import generate_progression_wav
from cadence.chord_model import (
    DEFAULT_MODEL_PATH,
    ChordEvent,
    ChordModelError,
)
from cadence.chart_data import (
    ChartChord,
    ChartData,
    ChartDataError,
    ChartGroup,
    SectionRange,
    bar_beat_slots,
    build_chart_data,
    first_chord_start,
    format_bar_measure,
    total_bar_count,
)
from cadence.chart_editing import (
    BeatCellEditError,
    apply_beat_cell_edits,
    default_beat_cells,
)
from cadence.chart_pdf import create_chart_pdf
from cadence.feedback import FeedbackSaveError, save_feedback_example
from cadence.matching import ProgressionCandidate
from cadence.progression_data import (
    FREQUENCY_GROUPS,
    Progression,
    load_progressions,
    search_progressions,
)
from cadence.song_analysis import AudioAnalysisError, SongAnalysis, analyze_audio_bytes
from cadence.song_metadata import KEY_CHOICES, TIME_SIGNATURES, bar_beat_position
from cadence.theory import (
    MAJOR_KEYS,
    diatonic_chords,
    major_scale,
    note_pitch_class,
    spell_progression,
)

APP_ROOT = Path(__file__).resolve().parent
_FREQUENCY_STYLES = {
    "frequent": ("Frequent", "frequent"),
    "medium": ("Medium", "medium"),
    "less common": ("Less common", "less-common"),
}
_CIRCLE_OF_FIFTHS = ("C", "G", "D", "A", "E", "B", "F#", "C#", "G#", "D#", "A#", "F")
_CIRCLE_OF_FOURTHS = ("C", "F", "Bb", "Eb", "Ab", "Db", "Gb", "B", "E", "A", "D", "G")
_PROGRESSION_HIGHLIGHT_COLORS = (
    "#f4c56a",
    "#80c8ed",
    "#93d6a6",
    "#f29c9c",
    "#c2a5e8",
    "#f3a9cf",
    "#7ed7d2",
    "#f4ae73",
    "#d3d878",
    "#a2b8f5",
    "#dca2b9",
    "#c5b28e",
    "#91c2ae",
)


def _keyboard_svg(scale_notes: tuple[str, ...] | None = None) -> str:
    scale_pitch_classes = {
        note_pitch_class(note) for note in (scale_notes or ())
    }
    white_notes = ("C", "D", "E", "F", "G", "A", "B")
    white_width = 48
    black_width = 30
    white_keys = []
    for index, note in enumerate(white_notes):
        highlighted = note_pitch_class(note) in scale_pitch_classes
        stroke = "#bd8640" if highlighted else "#383129"
        fill = "#d9a85f" if highlighted else "#f3e7cf"
        x = index * white_width
        white_keys.append(
            f'<rect x="{x}" y="0" width="{white_width}" height="128" '
            f'rx="3" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="{3 if highlighted else 1}"/>'
            f'<text x="{x + white_width / 2}" y="116" text-anchor="middle" '
            f'font-size="13" fill="#211f1b">{note}</text>'
        )

    black_keys = []
    for position, note in ((0, "C#"), (1, "D#"), (3, "F#"), (4, "G#"), (5, "A#")):
        highlighted = note_pitch_class(note) in scale_pitch_classes
        fill = "#bd8640" if highlighted else "#292621"
        text_fill = "#211f1b" if highlighted else "#fff8e8"
        x = (position + 1) * white_width - black_width / 2
        black_keys.append(
            f'<rect x="{x}" y="0" width="{black_width}" height="78" '
            f'rx="3" fill="{fill}" stroke="#171613" '
            f'stroke-width="{3 if highlighted else 1}"/>'
            f'<text x="{x + black_width / 2}" y="67" text-anchor="middle" '
            f'font-size="9" fill="{text_fill}">{note}</text>'
        )
    image_label = (
        "Piano keyboard with scale notes highlighted"
        if scale_notes
        else "Piano keyboard with note names and no scale highlights"
    )
    return (
        '<svg viewBox="0 0 336 132" role="img" '
        f'aria-label="{image_label}" '
        'style="width:100%;max-width:520px;height:auto">'
        + "".join(white_keys)
        + "".join(black_keys)
        + "</svg>"
    )


def _circle_svg(
    note_order: tuple[str, ...],
    highlighted_notes: tuple[str, ...],
    interval_name: str,
) -> str:
    highlighted_pitch_classes = {
        note_pitch_class(note) for note in highlighted_notes
    }
    nodes = []
    for index, note in enumerate(note_order):
        angle = math.radians(-90 + index * 30)
        x = 150 + 105 * math.cos(angle)
        y = 132 + 105 * math.sin(angle)
        active = note_pitch_class(note) in highlighted_pitch_classes
        fill = "#bd8640" if active else "#302c25"
        text_fill = "#211f1b" if active else "#f3e7cf"
        nodes.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="18" fill="{fill}" '
            'stroke="#d9a85f"/>'
            f'<text x="{x:.1f}" y="{y + 4:.1f}" text-anchor="middle" '
            f'font-size="11" fill="{text_fill}">{note}</text>'
        )
    return (
        '<svg viewBox="0 0 300 264" role="img" '
        f'aria-label="Circle of {interval_name}s with selected notes highlighted" '
        'style="width:100%;max-width:360px;height:auto">'
        '<circle cx="150" cy="132" r="105" fill="none" stroke="#74664e" '
        'stroke-width="1.5"/>'
        + "".join(nodes)
        + "</svg>"
    )


def _render_circle_diagram(
    interval_name: str,
    note_order: tuple[str, ...],
    highlighted_notes: tuple[str, ...],
    explanation: str,
) -> None:
    st.markdown(
        _circle_svg(note_order, highlighted_notes, interval_name),
        unsafe_allow_html=True,
    )
    st.caption(explanation)


def _frequency_badge(frequency: str) -> str:
    label, style = _FREQUENCY_STYLES[frequency]
    return f'<span class="frequency-badge {style}">{label}</span>'


def _set_tutorial_step(step: int) -> None:
    st.session_state.tutorial_step = step


def _initialize_state() -> None:
    defaults: dict[str, object] = {
        "page": "welcome",
        "experience": None,
        "search_query": "",
        "frequency_filter": "All",
        "selected_progression_id": None,
        "tutorial_step": 0,
        "analysis_result": None,
        "analysis_file_hash": None,
        "analysis_title": "",
        "analysis_key": None,
        "analysis_tempo": None,
        "analysis_time_signature": None,
        "analysis_sections": [],
        "analysis_layout": None,
        "analysis_chart_preview": None,
        "analysis_chart_signature": None,
        "analysis_chart_layout_signature": None,
        "analysis_edit_mode": False,
        "analysis_chart_undo_available": False,
        "analysis_scroll_to_feedback": False,
        "analysis_beat_cell_values": {},
        "analysis_feedback_original_events": (),
        "analysis_feedback_corrected_events": (),
        "analysis_feedback_rights_confirmed": False,
        "analysis_feedback_id": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _navigate(page: str) -> None:
    st.session_state.page = page
    st.rerun()


def _open_lesson_query(progressions: tuple[Progression, ...]) -> None:
    progression_id = st.query_params.get("lesson")
    if progression_id is None:
        return
    progression = next(
        (item for item in progressions if item.id == progression_id),
        None,
    )
    if progression is None:
        st.error("That progression lesson link is not available.")
        return
    st.session_state.selected_progression_id = progression.id
    st.session_state.page = "lesson"
    del st.query_params["lesson"]
    st.rerun()


def _apply_styles() -> None:
    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"] {
            background: radial-gradient(ellipse at top, #332a1f 0%, #191815 48%);
        }
        [data-testid="stHeader"] { background: transparent; }
        h1, h2, h3 { color: #f3e7cf; }
        [data-testid="stSidebar"] { background: #211f1b; }
        .cadence-eyebrow {
            color: #d9a85f;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.16em;
            text-transform: uppercase;
        }
        .cadence-note {
            color: #d6cbb7;
            font-size: 0.95rem;
        }
        .cadence-hello {
            color: #f3e7cf;
            animation: hello-arrive 0.9s ease-out both;
        }
        @keyframes hello-arrive {
            from { opacity: 0; transform: translateY(12px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .frequency-badge {
            display: inline-block;
            border: 1px solid currentColor;
            border-radius: 999px;
            padding: 0.18rem 0.65rem;
            font-size: 0.82rem;
            font-weight: 700;
        }
        .frequency-badge.frequent { color: #8fd3a8; }
        .frequency-badge.medium { color: #f0ce76; }
        .frequency-badge.less-common { color: #f28b82; }
        .chart-measure-row {
            align-items: flex-start;
            color: #f3e7cf;
            display: flex;
            flex-wrap: wrap;
            gap: 0.8rem 1.1rem;
            margin: 0.5rem 0 1rem;
        }
        .chart-measure {
            min-width: 10rem;
        }
        .chart-measure-number {
            color: #d9a85f;
            font-size: 0.75rem;
            margin: 0 0 0.2rem 0.2rem;
        }
        .chart-measure-content {
            align-items: center;
            border-left: 2px solid #d9a85f;
            border-right: 2px solid #d9a85f;
            display: flex;
            font-family: monospace;
            justify-content: space-around;
            min-height: 2.1rem;
            padding: 0.1rem 0.35rem;
            white-space: nowrap;
        }
        .chart-measure-content .chart-match {
            border-radius: 0.3rem;
            border: 1px solid #211f1b;
            color: #211f1b;
            display: inline-block;
            font-weight: 700;
            padding: 0.1rem 0.2rem;
        }
        .chart-match-link {
            display: inline-flex;
            text-decoration: none;
        }
        .chart-match-link:focus-visible {
            outline: 2px solid #68430f;
            outline-offset: 2px;
        }
        .chart-measure-content .chart-chord {
            display: inline-block;
            padding: 0.1rem 0.2rem;
        }
        .chart-hover-match {
            display: inline-flex;
            position: relative;
        }
        .chart-hover-match .chart-tooltip {
            background: #f3e7cf;
            border: 1px solid #bd8640;
            border-radius: 0.45rem;
            box-shadow: 0 0.4rem 1rem #0009;
            color: #211f1b;
            display: none;
            font-family: sans-serif;
            font-size: 0.8rem;
            left: 50%;
            max-height: 16rem;
            min-width: 12rem;
            overflow-y: auto;
            padding: 0.55rem 0.7rem;
            position: absolute;
            top: 100%;
            transform: translateX(-50%);
            white-space: normal;
            z-index: 1000;
        }
        .chart-tooltip-candidate {
            align-items: center;
            display: flex;
            gap: 0.4rem;
            margin: 0.2rem 0;
        }
        .chart-tooltip-swatch {
            border: 1px solid #211f1b;
            border-radius: 0.15rem;
            flex: 0 0 0.8rem;
            height: 0.8rem;
        }
        .chart-hover-match:hover .chart-tooltip,
        .chart-hover-match:focus-within .chart-tooltip {
            display: block;
        }
        .chart-tooltip a {
            color: #68430f;
            display: inline-block;
            font-weight: 700;
            margin-top: 0.3rem;
        }
        .stButton > button {
            border-color: #bd8640;
            border-radius: 0.7rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_navigation() -> None:
    if st.session_state.page == "welcome":
        return
    with st.sidebar:
        st.markdown("### Cadence")
        st.caption("Resolve every song.")
        if st.button("Home", use_container_width=True):
            _navigate("home")
        if st.button("Progression library", use_container_width=True):
            _navigate("library")
        if st.button("Analyze a song", use_container_width=True):
            _navigate("analysis")
        st.divider()
        st.caption("Frequency groups are curated learning guidance.")


def _render_welcome() -> None:
    st.markdown('<p class="cadence-eyebrow">Learn the movement</p>', unsafe_allow_html=True)
    st.title("Cadence")
    st.subheader("Discover why familiar chord progressions work.")
    st.write(
        "Start with a short major-scale primer, or head straight to the "
        "progression library."
    )
    beginner, experienced = st.columns(2)
    with beginner:
        st.markdown("#### New to music theory?")
        if st.button("Start with the beginner primer", type="primary"):
            st.session_state.experience = "beginner"
            st.session_state.tutorial_step = 0
            _navigate("tutorial")
    with experienced:
        st.markdown("#### Already have some experience?")
        if st.button("Go straight to Cadence"):
            st.session_state.experience = "experienced"
            _navigate("home")


def _render_home() -> None:
    st.markdown('<p class="cadence-eyebrow">Your learning space</p>', unsafe_allow_html=True)
    st.title("Where would you like to start?")
    if st.session_state.experience == "beginner":
        st.caption("You can revisit the beginner primer, or choose a learning space below.")
        if st.button("Open the major-scale primer"):
            st.session_state.tutorial_step = 0
            _navigate("tutorial")
    library, analysis = st.columns(2)
    with library:
        st.markdown("### Explore progressions")
        st.write("Search curated patterns, hear a synthetic example, and see how the chords fit a major key.")
        if st.button("Browse the progression library", type="primary"):
            _navigate("library")
    with analysis:
        st.markdown("### Analyze a local song")
        st.write("Use an authorized recording to explore experimental chord estimates.")
        if st.button("Open song analysis"):
            _navigate("analysis")


def _render_tutorial() -> None:
    step = st.session_state.tutorial_step
    step_count = 7
    st.markdown('<p class="cadence-eyebrow">A short music primer</p>', unsafe_allow_html=True)
    st.progress((step + 1) / step_count)
    st.caption(f"Step {step + 1} of {step_count}")

    if step == 0:
        st.markdown('<h1 class="cadence-hello">Hello, music explorer!</h1>', unsafe_allow_html=True)
        st.write("Let's see how notes become scales, and scales become chords.")
    elif step == 1:
        st.title("The major-scale recipe")
        st.write(
            "Before looking at a scale, learn its spacing pattern. W means a whole "
            "step; H means a half step."
        )
        st.markdown("### W – W – H – W – W – W – H")
        st.info(
            "A whole step skips one piano key. A half step moves to the very next "
            "key, whether black or white."
        )
    elif step == 2:
        st.title("Meet the piano notes")
        st.write(
            "The note names repeat across the keyboard. Compare the same keys before "
            "and after highlighting C major."
        )
        plain_column, scale_column = st.columns(2)
        with plain_column:
            st.markdown("**Piano key names**")
            st.markdown(_keyboard_svg(), unsafe_allow_html=True)
        with scale_column:
            st.markdown("**C major highlighted**")
            st.markdown(_keyboard_svg(major_scale("C")), unsafe_allow_html=True)
        st.caption(
            "The first keyboard shows the piano's usual key colors. Gold keys in the "
            "second diagram are the notes in C major."
        )
    elif step == 3:
        st.title("One scale pattern, different starting notes")
        st.write(
            "C major and D major use the same spacing pattern, but start on different "
            "notes. D major therefore includes F# and C# where C major has F and C."
        )
        c_column, d_column = st.columns(2)
        with c_column:
            st.markdown("**C major**")
            st.markdown(_keyboard_svg(major_scale("C")), unsafe_allow_html=True)
            st.caption("C – D – E – F – G – A – B")
        with d_column:
            st.markdown("**D major**")
            st.markdown(_keyboard_svg(major_scale("D")), unsafe_allow_html=True)
            st.caption("D – E – F# – G – A – B – C#")
        st.caption("Both follow W–W–H–W–W–W–H.")
    elif step == 4:
        st.title("Build the chords from C major")
        st.write(
            "Stack every other scale note to build a three-note chord on each scale "
            "step. Uppercase numerals are major, lowercase are minor, and ° is diminished."
        )
        columns = st.columns(7)
        for column, chord in zip(columns, diatonic_chords("C"), strict=True):
            with column:
                st.markdown(f"#### {chord.roman_numeral}")
                st.write(chord.symbol)
                st.caption(" – ".join(chord.notes))
                st.caption(chord.quality)
    elif step == 5:
        st.title("Circle of fifths")
        st.write(
            "This map puts related note roots next to each other. Moving clockwise "
            "raises the root by a fifth; musicians use it to see how progressions move "
            "between related chords and keys."
        )
        _render_circle_diagram(
            "fifth",
            _CIRCLE_OF_FIFTHS,
            ("D", "G", "C"),
            "In ii–V–I, D → G → C moves counterclockwise by descending fifths; the last "
            "step reaches the home chord C.",
        )
    else:
        st.title("Circle of fourths")
        st.write(
            "This is the same set of roots read in the opposite direction. Moving "
            "clockwise raises the root by a fourth, which makes the upward motion in "
            "progressions such as ii–V–I easy to follow."
        )
        _render_circle_diagram(
            "fourth",
            _CIRCLE_OF_FOURTHS,
            ("D", "G", "C"),
            "D → G → C moves clockwise by ascending fourths and resolves to C.",
        )

    st.caption("This is a learning guide, not a quiz.")
    if step < step_count - 1:
        back_column, next_column, skip_column = st.columns(3)
        with back_column:
            st.button(
                "Back",
                disabled=step == 0,
                on_click=_set_tutorial_step,
                args=(max(0, step - 1),),
            )
        with next_column:
            st.button(
                "Next",
                type="primary",
                on_click=_set_tutorial_step,
                args=(step + 1,),
            )
        with skip_column:
            if st.button("Skip the primer"):
                _navigate("home")
    else:
        back_column, finish_column = st.columns(2)
        with back_column:
            st.button(
                "Back",
                on_click=_set_tutorial_step,
                args=(step - 1,),
            )
        with finish_column:
            if st.button("Continue to Cadence", type="primary"):
                _navigate("home")


def _render_library(progressions: tuple[Progression, ...]) -> None:
    st.markdown('<p class="cadence-eyebrow">The progression databank</p>', unsafe_allow_html=True)
    st.title("Find a progression")
    st.caption(
        "Groups are curated learning guidance, not measured song counts. Green is frequent, "
        "yellow is medium, and red is less common."
    )
    search_column, filter_column = st.columns([3, 1])
    with search_column:
        query = st.text_input(
            "Search by name or Roman-numeral pattern",
            key="search_query",
            placeholder="Try: ii-V-I",
        )
    with filter_column:
        frequency = st.selectbox(
            "Frequency group",
            ("All", *FREQUENCY_GROUPS),
            key="frequency_filter",
        )

    matches = search_progressions(
        progressions,
        query=query,
        frequency=None if frequency == "All" else frequency,
    )
    if not matches:
        st.info("No progressions found. Try another name or Roman-numeral pattern.")
        return

    for start in range(0, len(matches), 2):
        columns = st.columns(2)
        for column, progression in zip(columns, matches[start : start + 2]):
            with column:
                with st.container(border=True):
                    st.markdown(f"### {progression.name}")
                    st.markdown(f"**{progression.pattern}**")
                    st.markdown(
                        _frequency_badge(progression.frequency),
                        unsafe_allow_html=True,
                    )
                    if st.button(
                        "Open lesson",
                        key=f"open-{progression.id}",
                        use_container_width=True,
                    ):
                        st.session_state.selected_progression_id = progression.id
                        _navigate("lesson")


def _render_lesson(progressions: tuple[Progression, ...]) -> None:
    selected_id = st.session_state.selected_progression_id
    progression = next(
        (entry for entry in progressions if entry.id == selected_id),
        None,
    )
    if progression is None:
        st.error("That progression is not in the catalog. Return to the library and choose another.")
        if st.button("Back to the progression library"):
            _navigate("library")
        return

    st.markdown('<p class="cadence-eyebrow">Progression lesson</p>', unsafe_allow_html=True)
    st.title(progression.name)
    st.markdown(f"**{progression.pattern}**")
    st.markdown(
        _frequency_badge(progression.frequency),
        unsafe_allow_html=True,
    )
    st.write(progression.description)
    st.write(progression.theory_relationship)

    st.subheader("Hear the movement in C major")
    spelled = spell_progression(
        progression.degrees,
        "C",
        progression.qualities,
    )
    flow = st.columns(len(spelled) * 2 - 1)
    for index, chord in enumerate(spelled):
        with flow[index * 2]:
            with st.container(border=True):
                st.markdown(f"#### {chord.roman_numeral}")
                st.write(chord.symbol)
                st.caption(" - ".join(chord.notes))
        if index < len(spelled) - 1:
            with flow[index * 2 + 1]:
                st.markdown("<div style='padding-top:1.5rem'>→</div>", unsafe_allow_html=True)

    st.audio(
        generate_progression_wav(
            progression.degrees,
            qualities=progression.qualities,
        ),
        format="audio/wav",
    )
    st.caption(
        "Piano-like synthetic tones illustrate the chords; they are not recorded or "
        "sampled piano sounds."
    )

    root_sequence = tuple(chord.notes[0] for chord in spelled)
    st.subheader("Circle of fifths")
    _render_circle_diagram(
        "fifth",
        _CIRCLE_OF_FIFTHS,
        root_sequence,
        "Each highlighted note is a chord root. Neighboring positions are a perfect fifth "
        "apart; moving the other direction gives fourths.",
    )

    st.subheader("Chord spellings in all 12 major keys")
    spelling_rows = []
    for key in MAJOR_KEYS:
        chords = spell_progression(
            progression.degrees,
            key,
            progression.qualities,
        )
        row: dict[str, str] = {"Key": key}
        for roman, chord in zip(progression.roman_numerals, chords, strict=True):
            row[roman] = f"{chord.symbol} ({' - '.join(chord.notes)})"
        spelling_rows.append(row)
    st.table(spelling_rows)
    if st.button("Back to the progression library"):
        _navigate("library")


def _metadata_strength(value: float) -> str:
    if value < 0.05:
        return "low"
    if value < 0.2:
        return "tentative"
    return "stronger, but still heuristic"


def _set_analysis_result(
    uploaded_file: UploadedFile,
    progressions: tuple[Progression, ...],
) -> None:
    audio_bytes = uploaded_file.getvalue()
    st.session_state.analysis_result = None
    try:
        result = analyze_audio_bytes(
            audio_bytes,
            uploaded_file.name,
            DEFAULT_MODEL_PATH,
            progressions,
        )
    except (AudioAnalysisError, ChordModelError) as exc:
        st.error(str(exc))
        return

    st.session_state.analysis_result = result
    st.session_state.analysis_file_hash = hashlib.sha256(audio_bytes).hexdigest()
    st.session_state.analysis_edit_mode = False
    st.session_state.analysis_chart_undo_available = False
    st.session_state.analysis_scroll_to_feedback = False
    st.session_state.analysis_beat_cell_values = {}
    st.session_state.analysis_feedback_original_events = ()
    st.session_state.analysis_feedback_corrected_events = ()
    st.session_state.analysis_feedback_rights_confirmed = False
    st.session_state.analysis_feedback_id = None
    st.session_state.analysis_title = ""
    st.session_state.analysis_key = result.metadata.key
    st.session_state.analysis_tempo = (
        round(result.metadata.tempo_bpm, 1)
        if result.metadata.tempo_bpm is not None
        else 120.0
    )
    st.session_state.analysis_time_signature = result.metadata.time_signature
    st.session_state.analysis_layout = None
    st.session_state.analysis_chart_preview = None
    st.session_state.analysis_chart_signature = None
    st.session_state.analysis_chart_layout_signature = None
    for key in list(st.session_state.keys()):
        if key.startswith(
            (
                "analysis_section_name_",
                "analysis_section_start_",
                "analysis_section_end_",
                "analysis_beat_edit_",
            )
        ):
            del st.session_state[key]
    tempo = float(st.session_state.analysis_tempo)
    chart_start = first_chord_start(result.events, result.duration) or 0.0
    total_bars = total_bar_count(
        result.duration - chart_start,
        tempo,
        st.session_state.analysis_time_signature,
    )
    st.session_state.analysis_sections = [
        {"name": "Song", "start_bar": 1, "end_bar": total_bars, "whole_song": True}
    ]


def _render_analysis_sections(total_bars: int, layout_id: str) -> None:
    st.subheader("Song sections")
    st.caption(
        "Mark or edit sections yourself; Cadence does not automatically detect "
        "verse, chorus, or bridge boundaries."
    )
    updated_sections = []
    for index, section in enumerate(st.session_state.analysis_sections):
        name_key = f"analysis_section_name_{index}"
        start_key = f"analysis_section_start_{layout_id}_{index}"
        end_key = f"analysis_section_end_{layout_id}_{index}"
        if name_key not in st.session_state:
            st.session_state[name_key] = section["name"]
        if start_key not in st.session_state:
            st.session_state[start_key] = min(section["start_bar"], max(1, total_bars))
        st.session_state[start_key] = min(
            max(int(st.session_state[start_key]), 1),
            max(1, total_bars),
        )
        if end_key not in st.session_state:
            st.session_state[end_key] = section["end_bar"]
        st.session_state[end_key] = min(
            max(int(st.session_state[end_key]), int(st.session_state[start_key])),
            max(1, total_bars),
        )
        name_column, start_column, end_column = st.columns((2, 1, 1))
        with name_column:
            name = st.text_input(
                f"Section {index + 1} name",
                key=name_key,
            )
        with start_column:
            start_bar = st.number_input(
                "Start bar",
                min_value=1,
                max_value=max(1, total_bars),
                key=start_key,
            )
        with end_column:
            end_bar = st.number_input(
                "End bar",
                min_value=int(start_bar),
                max_value=max(1, total_bars),
                key=end_key,
            )
        updated_sections.append(
            {
                "name": name,
                "start_bar": int(start_bar),
                "end_bar": int(end_bar),
                "whole_song": (
                    section.get("whole_song", False)
                    and int(start_bar) == 1
                    and int(end_bar) == total_bars
                ),
            }
        )
    st.session_state.analysis_sections = updated_sections
    if st.button("Add section"):
        next_index = len(updated_sections)
        st.session_state.analysis_sections = updated_sections + [
            {
                "name": f"Section {next_index + 1}",
                "start_bar": 1,
                "end_bar": total_bars,
                "whole_song": True,
            }
        ]
        st.rerun()


def _beat_edit_key(bar_number: int, beat_number: int) -> str:
    return (
        f"analysis_beat_edit_{st.session_state.analysis_file_hash}_"
        f"{bar_number}_{beat_number}"
    )


def _store_beat_cell(address: tuple[int, int], widget_key: str) -> None:
    values = dict(st.session_state.analysis_beat_cell_values)
    values[address] = st.session_state[widget_key]
    st.session_state.analysis_beat_cell_values = values


def _current_beat_values(result: SongAnalysis) -> dict[tuple[int, int], str]:
    defaults = default_beat_cells(
        result.events,
        duration=result.duration,
        tempo_bpm=float(st.session_state.analysis_tempo),
        time_signature=st.session_state.analysis_time_signature,
    )
    values = dict(defaults)
    values.update(st.session_state.analysis_beat_cell_values)
    return {address: values[address] for address in defaults}


def _chart_input_signature(result: SongAnalysis) -> str:
    beat_defaults = default_beat_cells(
        result.events,
        duration=result.duration,
        tempo_bpm=float(st.session_state.analysis_tempo),
        time_signature=st.session_state.analysis_time_signature,
    )
    beat_values = _current_beat_values(result)
    signature = (
        st.session_state.analysis_file_hash,
        st.session_state.analysis_title.strip(),
        st.session_state.analysis_key,
        float(st.session_state.analysis_tempo),
        st.session_state.analysis_time_signature,
        tuple(
            (
                section["name"],
                int(section["start_bar"]),
                int(section["end_bar"]),
            )
            for section in st.session_state.analysis_sections
        ),
        tuple(
            sorted(
                (address, value)
                for address, value in beat_values.items()
                if value != beat_defaults[address]
            )
        ),
        result.metadata.beat_times,
    )
    return hashlib.sha256(repr(signature).encode("utf-8")).hexdigest()


def _chart_layout_signature(result: SongAnalysis) -> str:
    signature = (
        st.session_state.analysis_file_hash,
        float(st.session_state.analysis_tempo),
        st.session_state.analysis_time_signature,
        tuple(
            (
                section["name"],
                int(section["start_bar"]),
                int(section["end_bar"]),
            )
            for section in st.session_state.analysis_sections
        ),
        first_chord_start(result.events, result.duration),
    )
    return hashlib.sha256(repr(signature).encode("utf-8")).hexdigest()


def _matched_chord_html(
    label: str,
    candidates: tuple[ProgressionCandidate, ...],
    progression_colors: dict[str, str],
    link_progression: Progression | None = None,
) -> str:
    candidate_details = tuple(
        f"{candidate.progression.name} "
        f"({candidate.progression.pattern}) in {candidate.key}"
        for candidate in candidates
    )
    accessible_label = (
        f"{label}, possible progressions: {'; '.join(candidate_details)}"
    )
    candidate_colors = tuple(
        dict.fromkeys(
            progression_colors[candidate.progression.id]
            for candidate in candidates
        )
    )
    if len(candidate_colors) == 1:
        background = candidate_colors[0]
    else:
        segment_size = 100 / len(candidate_colors)
        stops = ", ".join(
            f"{color} {index * segment_size:g}% "
            f"{(index + 1) * segment_size:g}%"
            for index, color in enumerate(candidate_colors)
        )
        background = f"linear-gradient(90deg, {stops})"
    chord_markup = (
        '<span class="chart-match" '
        f'style="background: {escape(background)};">{escape(label)}</span>'
    )
    if link_progression is not None:
        lesson_link = f"?lesson={quote(link_progression.id, safe='')}"
        chord_markup = (
            f'<a class="chart-match-link" href="{lesson_link}" '
            f'aria-label="{escape(accessible_label)}, open progression lesson">'
            f"{chord_markup}</a>"
        )
    candidate_rows = "".join(
        '<div class="chart-tooltip-candidate">'
        f'<span class="chart-tooltip-swatch" '
        f'style="background-color: {progression_colors[candidate.progression.id]};">'
        "</span>"
        f"<span>{escape(details)}</span></div>"
        for candidate, details in zip(candidates, candidate_details, strict=True)
    )
    tooltip_heading = (
        "Possible progression"
        if len(candidates) == 1
        else "Possible progressions"
    )
    tooltip_link = ""
    if link_progression is not None:
        lesson_link = f"?lesson={quote(link_progression.id, safe='')}"
        tooltip_link = (
            f'<a href="{lesson_link}">Open progression lesson</a>'
        )
    return (
        '<span class="chart-hover-match" tabindex="0" '
        f'aria-label="{escape(accessible_label)}">'
        f"{chord_markup}"
        '<span class="chart-tooltip" role="tooltip">'
        f"<strong>{tooltip_heading}</strong>"
        f"{candidate_rows}"
        f"{tooltip_link}"
        "</span></span>"
    )


def _beat_cell_default(slot: tuple[ChartChord, ...]) -> str:
    labels = tuple(
        dict.fromkeys(chord.label for chord in slot if chord.label != "N")
    )
    if labels:
        return ", ".join(labels)
    return "N" if any(chord.label == "N" for chord in slot) else "."


def _progression_color_map(
    progressions: tuple[Progression, ...],
) -> dict[str, str]:
    return {
        progression.id: _PROGRESSION_HIGHLIGHT_COLORS[
            index % len(_PROGRESSION_HIGHLIGHT_COLORS)
        ]
        for index, progression in enumerate(progressions)
    }


def _render_chart_group(
    chart: ChartData,
    group: ChartGroup,
    show_match_highlights: bool,
    progression_colors: dict[str, str],
    edit_mode: bool = False,
) -> None:
    if not group.bars:
        return
    st.markdown(f"#### {escape(group.name)}")
    if group.match is not None and group.match.progression is not None:
        progression = group.match.progression
        st.success(
            f"Possible match in {group.name}: {progression.name} in "
            f"{group.match.key} (heuristic; review the chord estimates)."
        )
    elif group.match is not None and group.match.ambiguous:
        st.info(
            f"Possible progressions could fit {group.name}. Hover over colored "
            "chords to see which patterns they could belong to."
        )

    candidates_by_event: dict[
        int,
        dict[tuple[str, str], ProgressionCandidate],
    ] = {}
    if show_match_highlights and group.match is not None:
        for candidate in group.match.candidates:
            for event_index in candidate.matched_event_indices:
                candidates_by_event.setdefault(event_index, {})[
                    (candidate.progression.id, candidate.key)
                ] = candidate

    for row_start in range(0, len(group.bars), 4):
        bars = group.bars[row_start : row_start + 4]
        if edit_mode:
            bar_columns = st.columns(len(bars))
            for bar_column, bar in zip(bar_columns, bars, strict=True):
                with bar_column:
                    st.markdown(f"**Bar {bar.number}**")
                    beat_columns = st.columns(chart.beats_per_bar)
                    beat_slots = bar_beat_slots(
                        bar,
                        chart.beats_per_bar,
                        include_no_chord=True,
                    )
                    for beat_index, (beat_column, slot) in enumerate(
                        zip(beat_columns, beat_slots, strict=True),
                        start=1,
                    ):
                        with beat_column:
                            widget_key = _beat_edit_key(
                                bar.number,
                                beat_index,
                            )
                            address = (bar.number, beat_index)
                            defaults = st.session_state.analysis_beat_cell_values
                            if address not in defaults:
                                defaults = dict(defaults)
                                defaults[address] = _beat_cell_default(slot)
                                st.session_state.analysis_beat_cell_values = defaults
                            if (
                                widget_key not in st.session_state
                                or st.session_state[widget_key] != defaults[address]
                            ):
                                st.session_state[widget_key] = defaults[address]
                            st.text_input(
                                f"Bar {bar.number}, beat {beat_index} chord",
                                key=widget_key,
                                label_visibility="collapsed",
                                help=(
                                    "Type one supported chord symbol. Use N or . "
                                    "for no chord."
                                ),
                                on_change=_store_beat_cell,
                                args=(address, widget_key),
                            )
            continue

        row_html = []
        for bar in bars:
            beat_slots = bar_beat_slots(
                bar,
                chart.beats_per_bar,
                include_no_chord=True,
            )
            beat_html = []
            for slot in beat_slots:
                if not slot:
                    beat_html.append('<span class="chart-chord">.</span>')
                    continue
                labels: dict[
                    str,
                    dict[tuple[str, str], ProgressionCandidate],
                ] = {}
                for chord in slot:
                    if chord.label == "N":
                        continue
                    labels.setdefault(chord.label, {}).update(
                        candidates_by_event.get(chord.event_index, {})
                    )
                if not labels:
                    beat_html.append('<span class="chart-chord">.</span>')
                    continue
                rendered_labels = []
                for label, candidate_map in labels.items():
                    candidates = tuple(candidate_map.values())
                    if candidates:
                        link_progression = (
                            group.match.progression
                            if group.match is not None
                            else None
                        )
                        rendered_labels.append(
                            _matched_chord_html(
                                label,
                                candidates,
                                progression_colors,
                                link_progression=link_progression,
                            )
                        )
                    else:
                        rendered_labels.append(
                            f'<span class="chart-chord">{escape(label)}</span>'
                        )
                beat_html.append(
                    " / ".join(rendered_labels)
                )
            row_html.append(
                '<div class="chart-measure" '
                f'aria-label="{escape(format_bar_measure(bar, chart.beats_per_bar))}">'
                f'<div class="chart-measure-number">Bar {bar.number}</div>'
                '<div class="chart-measure-content">'
                + " ".join(beat_html)
                + "</div></div>"
            )
        st.markdown(
            '<div class="chart-measure-row">'
            + "".join(row_html)
            + "</div>",
            unsafe_allow_html=True,
        )


def _update_chart_preview(
    result: SongAnalysis,
    progressions: tuple[Progression, ...],
) -> bool:
    sections = tuple(
        SectionRange(
            name=section["name"],
            start_bar=section["start_bar"],
            end_bar=section["end_bar"],
        )
        for section in st.session_state.analysis_sections
    )
    try:
        beat_edits = apply_beat_cell_edits(
            result.events,
            _current_beat_values(result),
            duration=result.duration,
            tempo_bpm=float(st.session_state.analysis_tempo),
            time_signature=st.session_state.analysis_time_signature,
        )
        chart = build_chart_data(
            title=st.session_state.analysis_title,
            key=st.session_state.analysis_key,
            tempo_bpm=float(st.session_state.analysis_tempo),
            time_signature=st.session_state.analysis_time_signature,
            duration=result.duration,
            events=beat_edits.events,
            sections=sections,
            progressions=progressions,
            corrected_event_indices=beat_edits.corrected_event_indices,
            chart_start_seconds=beat_edits.chart_start_seconds,
        )
    except (BeatCellEditError, ChartDataError) as exc:
        st.error(str(exc))
        return False

    st.session_state.analysis_chart_preview = chart
    st.session_state.analysis_chart_signature = _chart_input_signature(result)
    st.session_state.analysis_chart_layout_signature = (
        _chart_layout_signature(result)
    )
    st.session_state.analysis_feedback_original_events = (
        beat_edits.original_feedback_events
    )
    st.session_state.analysis_feedback_corrected_events = (
        beat_edits.corrected_feedback_events
    )
    st.session_state.analysis_chart_undo_available = (
        beat_edits.changed_cell_count > 0
    )
    return True


def _undo_chart_edits(
    result: SongAnalysis,
    progressions: tuple[Progression, ...],
) -> bool:
    previous_values = st.session_state.analysis_beat_cell_values
    st.session_state.analysis_beat_cell_values = {}
    if not _update_chart_preview(result, progressions):
        st.session_state.analysis_beat_cell_values = previous_values
        return False
    st.session_state.analysis_edit_mode = False
    st.session_state.analysis_chart_undo_available = False
    st.session_state.analysis_feedback_original_events = ()
    st.session_state.analysis_feedback_corrected_events = ()
    st.session_state.analysis_feedback_rights_confirmed = False
    st.session_state.analysis_scroll_to_feedback = False
    return True


def _render_chart_preview(result: SongAnalysis, progressions: tuple[Progression, ...]) -> None:
    st.subheader("Section-aware chart preview")
    current_signature = _chart_input_signature(result)
    if st.button(
        "Update chart preview",
        type="primary",
        disabled=not st.session_state.analysis_title.strip(),
    ):
        _update_chart_preview(result, progressions)

    preview = st.session_state.analysis_chart_preview
    if preview is None:
        st.info(
            "Review the title, metadata, and section ranges, then update the preview "
            "to build the bar-and-beat chart."
        )
        return

    preview_is_current = (
        st.session_state.analysis_chart_signature == current_signature
    )
    if not preview_is_current:
        st.session_state.analysis_feedback_original_events = ()
        st.session_state.analysis_feedback_corrected_events = ()
    layout_is_current = (
        st.session_state.analysis_chart_layout_signature
        == _chart_layout_signature(result)
    )
    if not layout_is_current:
        st.session_state.analysis_edit_mode = False
    if preview_is_current:
        st.caption("Preview is up to date.")
    else:
        st.warning(
            "This is the previous chart preview. Your edits are not included yet; "
            "click **Update chart preview** before using lesson links or downloading."
        )
    st.markdown(f"### {escape(preview.title)}")
    if st.session_state.analysis_edit_mode:
        st.caption(
            "Type one chord symbol per beat. Enter N or . for no chord; empty "
            "beats are editable too. A change is placed at that beat's start. "
            "Click **Done editing** to apply valid changes to the preview."
        )
    st.caption(
        f"{escape(preview.key)} · {preview.tempo_bpm:g} BPM · "
        f"{escape(preview.time_signature)}"
    )
    if preview.chart_start_seconds is None:
        st.info(
            "No chord was predicted. Empty beats are shown as dots; the chart "
            "keeps the recording's full duration."
        )
    elif preview.chart_start_is_fixed:
        st.caption(
            f"Bar 1 stays anchored at the original chart start "
            f"({preview.chart_start_seconds:.2f}s); any earlier no-chord intro "
            "is excluded."
        )
    else:
        st.caption(
            f"Bar 1 starts at the first predicted chord "
            f"({preview.chart_start_seconds:.2f}s); any earlier no-chord intro "
            "is excluded."
        )
    progression_colors = _progression_color_map(progressions)
    for group in preview.groups:
        _render_chart_group(
            preview,
            group,
            show_match_highlights=preview_is_current,
            progression_colors=progression_colors,
            edit_mode=st.session_state.analysis_edit_mode,
        )

    edit_columns = st.columns((5, 1))
    with edit_columns[1]:
        if layout_is_current:
            button_label = (
                "Done editing" if st.session_state.analysis_edit_mode else "Edit chords"
            )
            if st.button(button_label, key="analysis_edit_chords"):
                if st.session_state.analysis_edit_mode:
                    if _update_chart_preview(result, progressions):
                        st.session_state.analysis_edit_mode = False
                        st.session_state.analysis_scroll_to_feedback = bool(
                            st.session_state.analysis_feedback_corrected_events
                        )
                        st.rerun()
                else:
                    st.session_state.analysis_edit_mode = True
                    st.rerun()
        else:
            st.caption("Update before editing")

    if preview_is_current:
        try:
            pdf_bytes = create_chart_pdf(preview)
        except RuntimeError as exc:
            st.error(str(exc))
        else:
            safe_title = "".join(
                character
                for character in preview.title
                if character.isalnum() or character in " -_"
            ).strip().replace(" ", "_")
            st.download_button(
                "Download performance chart PDF",
                data=pdf_bytes,
                file_name=f"{safe_title or 'cadence-chart'}.pdf",
                mime="application/pdf",
                key="chart_pdf_download",
            )
    else:
        st.download_button(
            "Download performance chart PDF",
            data=b"",
            file_name="cadence-chart.pdf",
            mime="application/pdf",
            disabled=True,
            key="chart_pdf_download_stale",
        )


def _render_song_analysis(
    result: SongAnalysis,
    progressions: tuple[Progression, ...],
    uploaded_file: UploadedFile,
) -> None:
    st.warning(
        "Chord, key, tempo, and time-signature values are experimental estimates. "
        "Classifier scores are heuristic, not calibrated probabilities."
    )
    metadata = result.metadata
    if metadata.tempo_bpm is None:
        st.info("No stable tempo estimate was found. Enter or confirm the tempo below.")

    key_column, tempo_column, meter_column = st.columns(3)
    with key_column:
        st.selectbox(
            "Key (estimated; correct as needed)",
            KEY_CHOICES,
            key="analysis_key",
        )
        st.caption(f"Key estimate strength: {_metadata_strength(metadata.key_strength)}.")
    with tempo_column:
        tempo = st.number_input(
            "Tempo in quarter-note BPM (estimated; correct as needed)",
            min_value=30.0,
            max_value=300.0,
            step=1.0,
            key="analysis_tempo",
        )
        st.caption(
            "Tempo estimate strength: "
            f"{_metadata_strength(metadata.tempo_strength)}."
        )
    with meter_column:
        st.selectbox(
            "Time signature (estimated; correct as needed)",
            TIME_SIGNATURES,
            key="analysis_time_signature",
        )
        st.caption(
            f"Meter estimate strength: {_metadata_strength(metadata.meter_strength)}."
        )

    st.text_input("Song title", key="analysis_title")
    if not st.session_state.analysis_title.strip():
        st.info("Add a song title before making a performance chart.")
    chart_start = first_chord_start(result.events, result.duration)
    chart_time_origin = chart_start if chart_start is not None else 0.0
    total_bars = total_bar_count(
        result.duration - chart_time_origin,
        float(tempo),
        st.session_state.analysis_time_signature,
    )
    layout = (
        float(tempo),
        st.session_state.analysis_time_signature,
        chart_start,
    )
    if st.session_state.analysis_layout != layout:
        adjusted_sections = []
        for index, section in enumerate(st.session_state.analysis_sections):
            if section.get("whole_song", False):
                start_bar = 1
                end_bar = total_bars
            else:
                start_bar = min(max(int(section["start_bar"]), 1), total_bars)
                end_bar = min(max(int(section["end_bar"]), start_bar), total_bars)
            adjusted_sections.append(
                {
                    "name": section["name"],
                    "start_bar": start_bar,
                    "end_bar": end_bar,
                    "whole_song": section.get("whole_song", False),
                }
            )
        st.session_state.analysis_sections = adjusted_sections
        st.session_state.analysis_layout = layout
    layout_id = f"{float(tempo):.3f}_{st.session_state.analysis_time_signature.replace('/', '_')}"
    _render_analysis_sections(total_bars, layout_id)

    st.subheader("Model chord estimates")
    st.caption(
        "Beat-cell edits appear in the chart after you update its preview."
    )
    if chart_start is not None:
        st.caption(
            "Bar and beat positions start at the first predicted chord; any earlier "
            "no-chord intro is excluded from the chart."
        )
    first_beat = (
        chart_start
        if chart_start is not None
        else (metadata.beat_times[0] if metadata.beat_times else 0.0)
    )
    chord_rows = []
    for event in result.events:
        if chart_start is not None and event.start_seconds < chart_start:
            continue
        bar, beat = bar_beat_position(
            event.start_seconds,
            float(tempo),
            st.session_state.analysis_time_signature,
            first_beat,
        )
        chord_rows.append(
            {
                "Chord": "·" if event.label == "N" else event.label,
                "Status": "Model estimate",
                "Start": f"{event.start_seconds:.2f}s",
                "End": f"{event.end_seconds:.2f}s",
                "Bar": bar,
                "Beat": beat,
                "Original model score": round(event.score, 3),
            }
        )
    if chord_rows:
        st.dataframe(chord_rows, use_container_width=True, hide_index=True)
    else:
        st.info("No chord spans were produced for this recording.")

    _render_chart_preview(result, progressions)
    _render_training_feedback(result, progressions, uploaded_file)


def _render_training_feedback(
    result: SongAnalysis,
    progressions: tuple[Progression, ...],
    uploaded_file: UploadedFile,
) -> None:
    original_events = st.session_state.analysis_feedback_original_events
    corrected_events = st.session_state.analysis_feedback_corrected_events
    changed_count = len(corrected_events)
    if not changed_count:
        return

    scroll_to_feedback = st.session_state.analysis_scroll_to_feedback
    scroll_markup = '<div id="cadence-training-feedback"></div>'
    if scroll_to_feedback:
        scroll_markup += (
            "<script>"
            "requestAnimationFrame(() => {"
            "document.getElementById('cadence-training-feedback')"
            "?.scrollIntoView({behavior: 'smooth', block: 'start'});"
            "});"
            "</script>"
        )
        st.session_state.analysis_scroll_to_feedback = False
    st.html(
        scroll_markup,
        unsafe_allow_javascript=scroll_to_feedback,
    )

    if (
        st.session_state.analysis_chart_undo_available
        and not st.session_state.analysis_feedback_id
    ):
        notice_column, undo_column = st.columns((4, 1))
        with notice_column:
            st.success(
                f"{changed_count} chord change"
                f"{'' if changed_count == 1 else 's'} applied."
            )
        with undo_column:
            if st.button(
                "Undo all changes",
                key="undo_chart_edits",
            ):
                if _undo_chart_edits(result, progressions):
                    st.rerun()
    elif st.session_state.analysis_feedback_id:
        st.info(
            "Chord changes are applied. Their saved training example is separate "
            "from the chart and is not removed by Undo."
        )

    st.subheader("Save corrections for a future training run")
    st.write(
        "Corrected chord intervals can become local training examples after the "
        "recording's rights and labels are reviewed. The model is not changed here."
    )
    st.caption(
        "This saves the full audio file locally but includes only manually changed "
        "chord intervals in its annotation file. Default training ignores it."
    )
    st.checkbox(
        "I own this recording or have permission to store and use it as local "
        "model-training data.",
        key="analysis_feedback_rights_confirmed",
    )
    if st.session_state.analysis_feedback_id:
        feedback_id = st.session_state.analysis_feedback_id
        st.caption(
            f"Saved locally as `{feedback_id}`. Further saves update this example."
        )
        st.write(
            "Review the audio and labels, add this ID to `training_song_ids` in "
            "`data/training/split.json` (never add the held-out song), then run:"
        )
        st.code(
            ".venv\\Scripts\\python.exe -m cadence.training "
            "--include-reviewed-feedback"
        )
    if st.button(
        "Save corrected intervals locally",
        disabled=not st.session_state.analysis_feedback_rights_confirmed,
        key="save_training_feedback",
    ):
        try:
            feedback_id = save_feedback_example(
                audio_bytes=uploaded_file.getvalue(),
                filename=uploaded_file.name,
                original_events=original_events,
                corrected_events=corrected_events,
                root=APP_ROOT,
                feedback_id=st.session_state.analysis_feedback_id,
            )
        except (FeedbackSaveError, OSError) as exc:
            st.error(f"Training feedback could not be saved: {exc}")
        else:
            st.session_state.analysis_feedback_id = feedback_id
            st.success(
                f"Saved {changed_count} corrected interval(s) locally as "
                f"`{feedback_id}`."
            )
            st.write(
                "Review the audio and labels, add this ID to `training_song_ids` "
                "in `data/training/split.json` (never add the held-out song), "
                "then run:"
            )
            st.code(
                ".venv\\Scripts\\python.exe -m cadence.training "
                "--include-reviewed-feedback"
            )


def _render_analysis(progressions: tuple[Progression, ...]) -> None:
    st.markdown('<p class="cadence-eyebrow">Local song workspace</p>', unsafe_allow_html=True)
    st.title("Analyze a local song")
    st.write(
        "Choose an audio file stored on this device. Cadence processes it locally "
        "and does not accept streaming links."
    )
    st.info("Only analyze audio you own or are otherwise authorized to use.")
    uploaded_file = st.file_uploader(
        "Local audio file",
        type=("wav", "mp3"),
        help="Supported formats: WAV and MP3. Full-band recordings are welcome.",
        key="song_audio_upload",
    )
    if uploaded_file is not None and st.button("Analyze recording", type="primary"):
        _set_analysis_result(uploaded_file, progressions)

    result = st.session_state.analysis_result
    if (
        result is not None
        and (
            uploaded_file is None
            or hashlib.sha256(uploaded_file.getvalue()).hexdigest()
            != st.session_state.analysis_file_hash
        )
    ):
        st.info(
            "The analyzed file is no longer selected or a different file is selected. "
            "Analyze it again before continuing."
        )
        result = None
    if result is not None:
        _render_song_analysis(result, progressions, uploaded_file)


def main() -> None:
    st.set_page_config(
        page_title="Cadence | Learn Progressions",
        page_icon="🎹",
        layout="wide",
    )
    _apply_styles()
    try:
        progressions = load_progressions(APP_ROOT / "data" / "progressions.json")
    except ValueError as exc:
        st.error(f"The progression library could not be loaded: {exc}")
        st.stop()

    _initialize_state()
    _open_lesson_query(progressions)
    _render_navigation()
    page = st.session_state.page
    if page == "welcome":
        _render_welcome()
    elif page == "home":
        _render_home()
    elif page == "tutorial":
        _render_tutorial()
    elif page == "library":
        _render_library(progressions)
    elif page == "lesson":
        _render_lesson(progressions)
    elif page == "analysis":
        _render_analysis(progressions)
    else:
        st.error(f"Unknown Cadence screen: {page!r}")
        if st.button("Return home"):
            _navigate("home")


if __name__ == "__main__":
    main()
