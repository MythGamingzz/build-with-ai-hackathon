---
doc: spec
status: approved
---

# Cadence — Technical Spec

## How This Works, In Plain Language

Cadence remains one small Python app that runs on the team's computer and opens in a browser. Its searchable progression library teaches the theory and plays original synthetic examples.

Before using the song analyzer, the project owner runs a training command on five original songs with their chord labels. The program turns short audio slices into a 12-number summary of the pitches they contain, teaches a small classifier which chord label goes with each summary, and tests it on one whole song it never saw. It also runs the existing chord-template analyzer on that same held-out song so the demo can show whether training helped. The command saves the trained model; visitors do not train it.

The browser app loads that saved model. When a visitor selects a local song, the app predicts chord labels, estimates the key, tempo, and time signature, and shows uncertainty. The visitor can correct the estimates, enter a title, mark song sections, and relabel chord events in the bar preview. Clicking **Update chart preview** turns those confirmed inputs into one validated bar-and-beat chart; later edits make that preview stale until it is updated again. The same confirmed chart powers the on-screen section groups, direct lesson links, progression matches, and downloadable PDF. Only after explicit rights confirmation can the visitor save the recording and corrected intervals locally for owner review; the model changes only after a separate, deliberate training run. No visitor audio is sent to a service.

The model is a small experiment, not a general music-recognition system. Five songs are enough to demonstrate the training process, but not enough to promise that it will work well on every style or recording.

## The Core Journey Through the System

PRD ref: `prd.md > The Core Journey`.

```text
Training and evaluation (project owner, before the demo)
Original songs + chord/time labels
    → extract pitch summaries for labeled audio frames
    → train a small classifier on four songs
    → compare classifier and existing template matcher on the fifth song
    → save the model artifact

Visitor app
Open Streamlit
    → choose experience and optionally take the scale tutorial
    → browse/search the progression databank and lessons
    → choose an authorized local song
    → load audio locally and predict chord labels
    → estimate key, tempo, and meter; visitor can correct them
    → visitor enters title and edits section names/bar ranges
    → finish chord editing to apply beat changes; update chart preview after metadata/section changes
    → review section-grouped bars/beats and match links
    → download a printable PDF from that confirmed preview
    → optionally open a plausible matching progression lesson
```

The five-song split is by complete song, never by random audio frames from the same song. One song is reserved for evaluation so the measured comparison is not simply testing on audio the model has already seen.

## Stack

- **Python 3.12:** Reuse the current project environment and code. The project already pins Python to 3.12.
- **Streamlit:** Local interactive browser app for the tutorial, library, analysis, chart preview, and PDF download. It keeps the Python model and interface together; the tradeoff is less precise layout control than a custom frontend. [Streamlit documentation](https://docs.streamlit.io/).
- **librosa (existing):** Load and analyze local audio, create chroma features, estimate tempo/beat positions, and support key/meter heuristics. [librosa documentation](https://librosa.org/doc/latest/index.html).
- **NumPy and SciPy (existing/transitive):** Numeric features and the existing chord smoothing helpers. [NumPy documentation](https://numpy.org/doc/stable/); [SciPy documentation](https://docs.scipy.org/doc/scipy/).
- **scikit-learn (new):** A small multinomial logistic-regression classifier trained on the labeled pitch summaries; no GPU or large neural-network framework. The accepted tradeoff is that a small training set may not generalize to different sounds or styles. [Logistic regression documentation](https://scikit-learn.org/stable/modules/linear_model.html#logistic-regression).
- **joblib (provided through scikit-learn):** Save and reload the small local model artifact. Load only the project's own trusted model file. [joblib documentation](https://joblib.readthedocs.io/en/stable/).
- **ReportLab (new):** Generate a real, multi-page downloadable PDF in memory without a web service. [ReportLab documentation](https://docs.reportlab.com/).
- **Python standard library `wave`:** Keep support for creating or validating generated WAV lesson examples. [Python `wave` documentation](https://docs.python.org/3/library/wave.html).
- **Tests:** Continue using `unittest`; cover label parsing, training/evaluation splits, feature/model behavior, metadata estimates, PDF output, progression matching, and existing analysis behavior.
- **No hosted model, external API, cloud storage, remote audio processing, account system, or platform download.**

The older `faster-whisper` lyric experiment and its CLI remain separate from the new app. The existing chord-template estimator remains available as the evaluation baseline; it is not the trained visitor-facing model.

## Where It Runs and How Someone Tries It

- **Runtime:** Local Streamlit process on the learner's Windows computer; the browser connects to `http://localhost:8501`.
- **Install/update dependencies:** From the project root, run `.venv\Scripts\python.exe -m pip install -e .`.
- **Show training and evaluation:** Run `.venv\Scripts\python.exe -m cadence.training`. The command reads the prepared annotations, trains on the four training songs, compares both methods on the held-out song, prints the measured results and limitations, then saves the model to `models\chord_classifier.joblib`.
- **Start the visitor app:** Run `.venv\Scripts\python.exe -m streamlit run app.py`, then use the browser tab it opens or navigate to `http://localhost:8501`.
- **Demo path:** Show the training command and output first; then show the app using the saved model, explore a progression lesson, analyze an authorized local song, correct metadata/sections, update and review the preview, then export the PDF.
- **Audio input:** Support full-song WAV and MP3 if the installed local decoder can read them. Verify MP3 support early. If decoding fails, show a clear supported-format error and do not show fabricated results.
- **Privacy and rights:** The learner confirmed the original training songs and performances may be public. Include only those five approved originals and their annotations; do not include the earlier copyrighted cover or private analysis artifacts. Visitor audio is processed locally, held in a temporary file only as needed, and removed after analysis unless the visitor explicitly confirms rights and saves corrected intervals. Opt-in audio and annotations remain under ignored `output/training-feedback/` and are never committed or uploaded.
- **Hackathon submission:** A short demo video and public GitHub repository are required. Deployment is optional; a local app is sufficient for the recording.

## Look and Feel

Carry forward `prd.md > Look and Feel` and `scope.md > Inspiration & Identity`: warm coffee/charcoal surfaces with amber, brass, and cream accents; minimal, readable layout; restrained music/café details. Keep chord estimates and metadata uncertainty prominent. The PDF uses a clean, high-contrast print layout rather than the app's dark theme, with clear title, key, tempo, time signature, sections, bar numbers, beat dots, and chord symbols.

Streamlit supports a theme and small CSS refinements, but not the layout freedom of a custom frontend. Prioritize a coherent library and chart preview over decoration.

## Components

### Streamlit App and Experience Choice

`app.py` presents experience choice, beginner tutorial, navigation to the databank or song analysis, and temporary session values for query, filter, selected lesson, uploaded analysis, corrected metadata and chord labels, draft section labels/ranges, and the confirmed chart preview. The preview is marked stale when its inputs change and must be updated before lesson links or PDF download. The default flow does not persist visitor audio. A separate opt-in action stores rights-cleared audio and corrected intervals under ignored `output/training-feedback/` for owner review; it never uploads or automatically trains on them. No user account or public song history.
Implements `prd.md > Experience choice and beginner tutorial`.

### Beginner Scale Tutorial

`app.py` presents a seven-step tutorial: animated greeting; W–W–H–W–W–W–H before any scale example; piano note names with unhighlighted and full-gold C-major-highlighted keyboard diagrams; C-major/D-major comparison; diatonic triad table; circle of fifths; and circle of fourths. The two circles and chord table have separate steps. Explain the circles as maps for seeing related roots and following common chord movement, with D–G–C shown as descending fifths and ascending fourths. Next/Back navigation is available throughout, with skip before the last step and one finish action at the end. The home screen retains its standard library action without a redundant skip button. It is content, not a quiz.
Implements `prd.md > Experience choice and beginner tutorial`.

### Progression Data and Databank

`data/progressions.json` holds stable IDs, names, Roman-numeral sequences, chord degrees and qualities, curated frequency groups, explanations, theory notes, and diagram data. It contains the diatonic starter set plus I–III–vi, I–III–IV, v–I–IV, and I–II–IV in the less-common group. `src/cadence/progression_data.py` validates and searches this content, then returns matches ordered by group. Frequency labels remain curated guidance, shown with both text and color.
Implements `prd.md > Searching and browsing the progression databank`.

### Scale and Key Theory

`src/cadence/theory.py` maps diatonic and specified major/minor triads to correctly spelled note names in all 12 major keys, including the raised/lowered chord tones in the four selected chromatic patterns. It provides the keyboard and circle-of-fifths pitch data; it does not infer a song key.
Implements `prd.md > Experience choice and beginner tutorial` and `prd.md > Understanding and hearing a progression`.

### Progression Lesson and Diagrams

`app.py` renders the selected progression's explanation, local circle-of-fifths diagram with progression roots highlighted, chord spellings across keys, quieter/spaced piano-like synthetic sample, and navigation back to the library. Diagrams are generated locally without remote assets.
Implements `prd.md > Understanding and hearing a progression`.

### Synthetic Audio Examples

`src/cadence/audio_examples.py` generates original WAV examples from the progression's chord degrees and qualities using a fundamental, soft harmonics, and an attack/decay envelope for a piano-like tone. Each chord is quieter, lasts longer, and has a silence gap before the next. These are synthesized, not recorded or sampled piano sounds.
Implements `prd.md > Understanding and hearing a progression`.

### Shared Audio Features and Existing Baseline

`src/cadence/audio_features.py` loads local audio as mono at a fixed sample rate and creates 12-bin chroma features with frame timestamps. It is shared by training, inference, and the existing baseline where practical. `src/cadence/chords.py` retains the current major/minor template matcher for baseline comparison and existing CLI behavior.
Implements `prd.md > Training and evaluating the chord model` and `prd.md > Analyzing a local song`.

### Training and Held-Out Evaluation

`src/cadence/training.py` reads `data/training/annotations.csv`. Each row identifies a song/audio file, start and end times, and a chord label. Feature-frame timestamps inside each labeled interval inherit that chord label; unlabeled gaps are ignored unless explicitly marked `N`. Normalize common flat spellings to the sharp-based chord labels already used by the baseline. Simplify seventh/sixth chords to the same-root major/minor triad and ignore slash-chord bass inversions; keep observed `Daug` and `Eaug` as their own augmented-triad labels. Validate missing audio, invalid/overlapping intervals, unsupported labels, and songs without usable labeled audio.

Use Demo 3 as the whole-song held-out evaluation set and the other four for training. Keep Demo 5 in the training set because it is the only recording with augmented chords; report that `Daug` and `Eaug` have examples from one song and cannot be independently evaluated on a held-out song. A small scikit-learn logistic-regression classifier learns from the chroma features. Train on the 24 major/minor triad labels, observed `Daug`/`Eaug` labels, and `N` (no chord); labels not represented in the training data cannot be learned, and other chord qualities are outside the first model's vocabulary.

Project both methods' predictions and the reference annotations onto the same feature-frame timestamps, and score only frames with reference labels. Apply the same temporal smoothing, short-run merging, and low-energy masking to both prediction streams before scoring. Print frame-level accuracy and macro-F1 so common chords do not hide errors on less frequent labels; count held-out labels absent from training as misses and report them separately. Do not claim a successful improvement unless the measured result supports it. Save the fitted model to `models/chord_classifier.joblib`; training is a project-owner command, not a visitor action.

An explicit `--include-reviewed-feedback` option reads local feedback manifests under ignored `output/training-feedback/`. It fails if feedback song IDs are not assigned to the training side of `data/training/split.json`, so the owner must review examples and preserve the held-out song before training. The default training command never reads these examples. Feedback stores only manually corrected intervals, not every model prediction, and retraining remains an explicit owner action.
Implements `prd.md > Training and evaluating the chord model`.

### Pre-Trained Chord Inference

`src/cadence/chord_model.py` loads the saved model artifact and predicts the chord label for each chroma frame. Smooth short runs using the existing helpers where appropriate, convert frames into chord events with start/end times, and retain a confidence-like model score only as a heuristic, not a calibrated probability. If the model artifact is absent or cannot be loaded, show an actionable error that points to the training command.
Implements `prd.md > Training and evaluating the chord model` and `prd.md > Analyzing a local song`.

### Song Metadata and Bar/Beat Alignment

`src/cadence/song_metadata.py` estimates:

- **Key:** Compare the song-wide chroma profile to major/minor key profiles and return the strongest candidate with heuristic uncertainty.
- **Tempo and beat times:** Use librosa beat tracking; tempo and beats are estimates.
- **Time signature:** Use beat-accent periodicity to suggest a common meter such as 3/4, 4/4, or 6/8. Resolve weak ties to a low-confidence 4/4 fallback rather than candidate-order 3/4. When a high-rate beat tracker follows eighth-note pulses in 6/8, infer the meter from those pulses and convert its tempo to quarter-note BPM for chart alignment. This heuristic is not reliable for every song; prompt the visitor to confirm or correct it.

The visitor can edit key, tempo, and time signature. They enter the song title and create or edit section names with bar ranges. Convert chord event times to bar/beat positions using the confirmed tempo and meter. Do not silently guess section boundaries. An explicit chart-preview update applies the edited values and refreshes all bar assignments; keep the previously generated preview visibly stale until then.
Implements `prd.md > Analyzing a local song`.

### Key-Independent Pattern Matching

`src/cadence/matching.py` removes no-chord spans, collapses consecutive duplicate chord labels, and compares ordered chord windows against each starter Roman-numeral pattern transposed into all 12 major keys. Run matching separately within each confirmed section and retain each exact candidate's pattern, implied key, and matched event positions. This is a heuristic match, not a separate trained progression model; do not rank candidates or present them as confidence values. If one candidate remains, the chart can link its highlighted chords to the lesson. If several candidates fit, show all their colored highlights and reveal the candidate list on hover; if none fit, leave the chart unhighlighted.
Implements `prd.md > Analyzing a local song`.

### Chart Data and Section Preview

`src/cadence/chart_editing.py` validates one typed chord value per beat cell. Supported chord symbols are accepted; `N` and `.` both mean no chord. If a cell changes, replace its events with a correction at the start of that beat, making it possible to move a chord to another beat or bar by editing both cells. Preserve unchanged predictions and create local training annotations only for corrected beat intervals after explicit rights confirmation. `src/cadence/chart_data.py` converts those events, corrected metadata, and manually entered section ranges into one validated chart model shared by the app preview and PDF. Each bar contains beat-positioned chord labels, their source-event indices, and flags for cells belonging to one or more exact progression candidates. Reject invalid or overlapping section ranges with an actionable message and include bars outside named ranges in an unsectioned group. Start bar 1 at the first predicted chord and omit earlier no-chord events; when there is no predicted chord, retain the full duration and render every empty beat as a dot. The Streamlit app shows section groups as measures with one amber boundary on each side, places chord names on their estimated beats, and fills empty beats—including `N` predictions—with dots; bar numbers appear above measures, not beside chord names. Show all exact candidates in the interactive preview using stable progression colors; blend colors for shared chords and list their patterns and keys on hover. Keep the PDF plain with no progression highlights. Do not add per-chord asterisks to the chart or PDF. Only unique matches link directly to their progression lesson. Clicking **Done editing** validates cell values, updates the chart and per-section matches immediately, exits edit mode only on success, shows one undo action for all unsaved chord changes, and scrolls to the correction-saving section; invalid values leave the visitor in edit mode with an actionable error. Undo rebuilds the preview from original model events and clears unsaved correction feedback. After a correction is saved locally, Undo does not remove that separately saved training example. **Update chart preview** applies other chart inputs such as metadata and section ranges. If any chart input changes afterward, mark the existing preview stale, suppress its lesson links and highlights, and disable PDF download until the changed inputs are applied.
Implements `prd.md > Analyzing a local song` and `prd.md > Exporting a performance chart`.

### Performance Chart PDF

`src/cadence/chart_pdf.py` builds the downloadable PDF in memory with ReportLab from the same confirmed chart model used by the preview. It lays out song title, corrected key/tempo/time signature, user-defined sections, numbered bars with single amber boundaries, chord labels on beat positions, and dots for empty beats. Keep the PDF plain: do not apply progression-match highlights or asterisks beside corrected chords. The app's color-coded candidate highlights, hover details, applied-changes notice, and undo action are interactive UI, not PDF content. Keep bar numbers separate from chord names. State that bar 1 starts at the first predicted chord and that any earlier no-chord intro is excluded; after a typed beat edit, state that the chart remains anchored at its original chart start. If no chord was predicted, disclose that the full duration is retained. Longer songs flow across readable landscape pages. Include a clear estimate disclaimer. Streamlit offers download only for the latest updated preview; a PDF error leaves the on-screen preview available and no chart is saved after the visitor leaves.
Implements `prd.md > Exporting a performance chart`.

### Tests

Use synthetic audio and small synthetic annotation tables for automated checks; do not make tests depend on the learner's recordings. Verify:

- Annotation parsing, interval validation, chord-label normalization (including augmented labels), and song-level split (no song appears in both training and holdout).
- The classifier can fit a known synthetic chord-feature set and produces labels in its supported vocabulary.
- Baseline and trained predictions are both scored against the same held-out labels.
- Chord event timing, candidate key/tempo/meter behavior, confidence/uncertain paths, and bar alignment.
- Pattern matching for known, ambiguous, and no-match sequences.
- Matching retains each candidate's key and exact event positions; ambiguous candidates remain unranked.
- Chart data covers correct beat slots, section grouping, invalid/overlapping ranges, per-section matches, all candidate highlight positions, no-chord dots, and first-chord bar anchoring.
- Interactive chart tests verify distinct progression colors, blended shared-cell highlights, and hover lists; PDF tests verify progression matches remain unhighlighted.
- Beat-cell editing accepts supported chord labels and `N`/`.` no-chord values, rejects invalid input, and moves a changed chord to the selected beat's start, including across a bar boundary.
- Corrected beat cells display without asterisks in both chart and PDF.
- Clicking **Done editing** applies valid cell edits and refreshes matches immediately, shows one undo for all unsaved edits, and scrolls to the correction-saving section; undo restores the original model estimates and clears the unsaved feedback. Invalid cells keep editing active and prevent stale preview/PDF use.
- Hovering a highlighted match shows its lesson details and the clickable lesson route; invalid lesson IDs show an actionable error.
- Preview inputs changing after an update mark it stale; only the updated preview can be downloaded.
- PDF output has a valid PDF header, includes the requested chart fields on manual inspection, highlights matched chords, and remains readable across multiple pages for long charts.
- Theory tests cover all-key spellings for the selected chromatic qualities; progression tests validate degree/quality/Roman-numeral agreement and group ordering; synthetic WAV tests verify quieter output and chord/rest timing; existing private CLI tests still pass.

Implements acceptance criteria from all `prd.md > Features and Behavior` headings.

## Data Model

- **Progression entry** (`data/progressions.json`): `id`, `name`, `roman_numerals`, `degrees`, `qualities`, `frequency`, `description`, `theory_relationship`, and optional diagram data. Checked-in educational content.
- **Training annotation** (`data/training/annotations.csv`): `song_id`, `audio_path`, `start_seconds`, `end_seconds`, and `chord_label`. The learner's chart is a human reference; it is converted to these timed labels before training. Audio and annotation assets are the five learner-approved original songs.
- **Train/holdout split** (`data/training/split.json`): song IDs assigned to the training set or the single held-out song. Split by song, not by audio frame.
- **Trained model** (`models/chord_classifier.joblib`): fitted classifier generated by the owner training command and loaded by the local app. Add a narrow `.gitignore` exception for this approved public artifact while keeping all other private `/models/` contents ignored, so a fresh checkout can run the analyzer without exposing unrelated model files.
- **Training report** (terminal output, optionally a generated report under ignored `output/`): training completion, held-out baseline/model scores, and data limitations.
- **Analysis result** (temporary Streamlit session state): estimated chord events, key, tempo, meter, confidence notes, and candidate progression matches. Visitor audio is not persisted by default.
- **Chord edits** (temporary Streamlit session state): text values keyed by bar and beat; supported labels or `N`/`.` for no chord. Edited cells become beat-aligned intervals, while unchanged events remain marked as estimates.
- **Opt-in training feedback** (local, ignored `output/training-feedback/<song-id>/`): explicitly rights-confirmed source audio plus CSV rows for only manually corrected beat intervals. The owner reviews these files, assigns eligible feedback song IDs to the training split, and uses `--include-reviewed-feedback` to train; default runs ignore them.
- **Chart inputs** (temporary session state): title, corrected metadata, and user-marked section names/bar ranges.
- **Confirmed chart preview** (temporary session state): validated bars/beats, section-specific progression matches and highlights, and the input signature used to detect stale edits. Generate PDF bytes only from this updated preview; clear with the session.
- **Session state:** experience choice, tutorial position, search query, frequency filter, selected lesson, analysis result, and chart edits. It ends with the browser session; there are no accounts or saved history.

## File Structure

```text
Build With AI/
├── app.py                              # Streamlit app and page rendering
├── .gitignore                          # Allow-list only the approved public model artifact
├── pyproject.toml                      # Python dependencies and training command
├── data/
│   ├── progressions.json               # Curated public progression lessons
│   └── training/
│       ├── annotations.csv              # Chord labels aligned to audio times
│       ├── split.json                   # Four train songs, one held-out song
│       └── audio/                       # Five learner-approved original tracks
├── models/
│   └── chord_classifier.joblib          # Saved model used by the app
├── src/cadence/
│   ├── audio_features.py                # Shared local audio loading/chroma
│   ├── audio_examples.py                # Synthetic WAV lesson examples
│   ├── chart_data.py                    # Validated bar/beat preview and section matches
│   ├── chart_editing.py                 # Typed beat-cell validation and interval corrections
│   ├── chart_pdf.py                     # Printable PDF generation from chart data
│   ├── progression_data.py              # Validated progression catalog and search
│   ├── chord_model.py                   # Load model and predict chord events
│   ├── chords.py                        # Existing template baseline and CLI support
│   ├── feedback.py                      # Explicit local storage of corrected training intervals
│   ├── matching.py                      # Pattern matching across 12 major keys
│   ├── song_metadata.py                 # Key, tempo, meter, and bar alignment
│   ├── theory.py                        # Major-scale qualities and chord spellings
│   ├── training.py                      # Training and held-out comparison command
│   ├── cli.py                           # Existing private analysis experiment
│   ├── comparison.py                    # Existing private experiment report logic
│   └── transcription.py                 # Existing private word-estimation component
├── tests/
│   ├── test_audio_features.py
│   ├── test_audio_examples.py
│   ├── test_chart_data.py
│   ├── test_chart_editing.py
│   ├── test_chart_pdf.py
│   ├── test_feedback.py
│   ├── test_chord_model.py
│   ├── test_matching.py
│   ├── test_progressions.py
│   ├── test_song_metadata.py
│   ├── test_theory.py
│   ├── test_training.py
│   ├── test_cli.py                    # Existing private-analysis tests
│   ├── test_chords.py                 # Existing template-estimator tests
│   ├── test_comparison.py             # Existing reference-report tests
│   └── test_transcription.py          # Existing transcription tests
├── recordings/                          # Existing ignored private experiments only
├── output/                              # Ignored reports and explicit local training feedback
└── devpost/                             # Scope, PRD, spec, and build checklist
```

## External Services and Dependencies

- **Streamlit:** Local UI only; no hosted Streamlit service. [Documentation](https://docs.streamlit.io/).
- **librosa:** Local audio decoding, chroma, beat tracking, and tempo estimate. [Documentation](https://librosa.org/doc/latest/index.html). Verify MP3 support early; do not imply a decoder lookup happened before testing it.
- **scikit-learn:** New local classifier dependency. [Documentation](https://scikit-learn.org/stable/).
- **joblib:** Local model persistence used by scikit-learn. [Documentation](https://joblib.readthedocs.io/en/stable/).
- **ReportLab:** New local PDF-generation dependency. [Documentation](https://docs.reportlab.com/).
- **NumPy/SciPy:** Existing numeric dependencies for feature and signal operations. [NumPy](https://numpy.org/doc/stable/); [SciPy](https://docs.scipy.org/doc/).
- **No external APIs, hosted model inference, credentials, cloud storage, analytics, or remote audio processing.**

## Important Failure Modes

- **Missing or inconsistent training annotations/audio** → stop training with a clear file/row error; do not save a success-shaped model.
- **Training data lacks chord labels or the held-out song contains labels absent from training** → report unsupported labels and the limitation; still compare only what can be measured without pretending the model knows unseen classes.
- **Saved model missing or incompatible** → app explains how to rerun the local training command; do not silently fall back to the old baseline as if it were the trained model.
- **Audio decoder fails or metadata estimate is weak** → show a clear file error or ask the visitor to correct key/tempo/meter before exporting.
- **Meter scores tie or remain weak** → suggest 4/4 with low confidence, never treat the candidate-order tie as evidence for 3/4.
- **Training-feedback consent is absent, no labels were changed, or a feedback song is not assigned to training** → do not save or train on it; explain the required owner review and split assignment.
- **PDF generation fails** → keep valid on-screen estimates available and explain the export failure.
- **Invalid beat cells, invalid/overlapping section ranges, or stale preview** → explain the problem; keep invalid beat cells editable and do not label stale chart data as current or enable its PDF download.
- **No plausible progression match** → show estimates without highlights. **Several exact matches** → show every candidate in the interactive preview and list them on hover without ranking or choosing one lesson.

## What Was Simplified and Why

- **Small supervised classifier on 12-bin chroma features** instead of a large neural network — it genuinely learns from labeled examples, is quick to run locally, and needs no GPU; it may not generalize beyond the five songs or their chord vocabulary.
- **Five songs with one whole-song holdout** instead of a large training corpus — enough to demonstrate training and a fair initial comparison, not enough to claim broad accuracy.
- **Major/minor triads, observed augmented labels, and no-chord** instead of all chord qualities — keeps the first label set bounded; seventh/sixth extensions and slash-bass inversions are simplified to root triads, while other qualities remain out of scope. Daug and Eaug appear only in Demo 5, so they cannot be evaluated on a separate held-out song.
- **Manual annotation table prepared from chord charts** instead of automatic PDF chart reading — the learner's chord chart supplies musical truth, while precise timed labels are the reliable training input.
- **User-marked song sections** instead of automatic structure detection — avoids adding a second ML problem.
- **Heuristic metadata suggestions with user correction** instead of an expert transcription engine — key, tempo, and meter remain estimates, particularly the time signature.
- **Local training command plus saved model artifact** instead of training whenever a visitor opens the app — training is demonstrable, but visitors can use the pre-trained model immediately.
- **ReportLab-generated chart PDF** instead of browser print styling — provides a consistent downloadable file offline, at the cost of one small dependency.
- **One local Streamlit app** instead of separate frontend, API, and hosted inference — reuses the team's Python experience and avoids services/accounts.
- **Curated static progression library and generated examples** instead of a database or commercial song samples — keeps the educational lesson rights-safe and small.

## Decisions and Open Issues

- **Learner choice — local Python web app:** Keep the previously selected Python 3.12 and Streamlit runtime; no deployment is needed for the demo.
- **Learner choice — model type:** Use a small supervised classifier trained from labeled audio features, not a large pretrained or hosted neural network.
- **Learner choice — chord labels:** Start with 24 major/minor triads and no-chord, and include observed Daug/Eaug as distinct augmented-triad labels. Simplify seventh/sixth extensions to their same-root major/minor triads and ignore slash-chord bass inversions. Both augmented labels appear only in Demo 5; keep it in training and disclose that cross-song performance is unmeasured. Other qualities are not claimed as supported.
- **Learner choice — training data:** Use five distinct original songs; reserve one complete song for evaluation and train on the other four.
- **Learner choice — baseline comparison:** Compare the trained classifier and existing template matcher against the same held-out song's reference labels; report the measured result even if training does not improve it.
- **Learner choice — labels:** Prepare a simple timed annotation table from chord charts; the model needs chord labels aligned to audio intervals, and automatic PDF input is deferred.
- **Learner choice — visitor experience:** Train before public use with a command-line run; include the resulting model for visitors to use without retraining.
- **Learner choice — time signature:** Suggest a common meter with uncertainty and let users correct it; time signature detection is heuristic.
- **Learner choice — PDF export:** Use a direct local PDF download with ReportLab; users manually supply title and song sections.
- **Learner feedback — chart preview:** Group bar/beat placements by manually confirmed sections, highlight only unique per-section progression matches with lesson links, require an explicit preview update after edits, and generate the PDF from that same confirmed chart data.
- **Verified — Demo 1 timing example:** The reference annotations place the bar-5 B-to-E change at 14.333s, the start of bar 6 at 90 BPM. The current model identifies E but starts it at 14.164s (0.169s early); the metadata estimate is 89.1 BPM. This is a beat/bar alignment issue, not a missing E chord label. The references already train the chord classifier; retraining alone is not evidence of improved transition placement. Keep the correction user-confirmed in the beat editor and evaluate any future automatic alignment separately.
- **Rights/privacy decision:** The learner confirmed their training recordings and performances are their own and may be publicly shared. Include only the five approved original songs and annotations in the public repository; never include the earlier copyrighted cover or local visitor feedback. Corrected visitor audio can be saved only after explicit rights confirmation, remains ignored and local, and requires owner review before a later training run.
- **Model artifact visibility:** Keep existing `/models/` ignore protection and allow-list only `models/chord_classifier.joblib`, which the learner wants available to app users.
- **Useful uncertainty — how a chart becomes model knowledge:** A chord name in a PDF is not enough by itself; training needs the corresponding audio interval. The agreed path is to prepare start/end times and chord labels from the chart, deriving approximate times from bars, tempo, and meter where the recording is steady.
- **Verified — MP3 support:** The installed local librosa decoder successfully read all five supplied MP3 recordings. Retain clear errors for unsupported or unreadable future files.
- **Verified — chart timing notes:** Pair `Solo_Demo_1.mp3` with `Chord Analysis Demo 1.pdf`; Demo 3's first numbered bar begins at approximately 00:00:12; Demo 4 bar 123 is F major and its corrected final bars are 147–149 in 6/8 at the charted 90 BPM. The measured pulse is approximately 89 BPM, which makes the corrected bar count broadly consistent with the 306.6-second recording; use approximate bar-derived timestamps and inspect alignment when preparing labels.
- **Open investigation — model performance:** The five-song data set may not beat the template baseline. The held-out comparison is the evidence; no minimum accuracy or improvement is promised.
- **Build check — training assets:** Verify audio file sizes, annotation coverage, and label overlap before the first training run. Keep training/test songs separate at song level.
- **Open content task:** Select a small set of less-common diatonic progressions while preparing the lesson content.
