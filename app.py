import math
from pathlib import Path

import streamlit as st

from cadence.audio_examples import generate_progression_wav
from cadence.progression_data import (
    FREQUENCY_GROUPS,
    Progression,
    load_progressions,
    search_progressions,
)
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
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _navigate(page: str) -> None:
    st.session_state.page = page
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


def _render_analysis_placeholder() -> None:
    st.markdown('<p class="cadence-eyebrow">Local song workspace</p>', unsafe_allow_html=True)
    st.title("Analyze a local song")
    st.info(
        "Song analysis is the next build slice. For now, explore the progression "
        "library; no audio is uploaded or processed on this screen."
    )
    st.caption("When analysis is added, use only audio you are authorized to analyze.")
    if st.button("Explore the progression library", type="primary"):
        _navigate("library")


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
        _render_analysis_placeholder()
    else:
        st.error(f"Unknown Cadence screen: {page!r}")
        if st.button("Return home"):
            _navigate("home")


if __name__ == "__main__":
    main()
