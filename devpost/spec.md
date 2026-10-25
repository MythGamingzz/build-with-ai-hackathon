---
doc: spec
status: approved
---

# Cadence — Technical Spec

## How This Works, In Plain Language

Cadence is a local Python experiment. It reads a short audio file of the learner's piano-and-vocal recording, runs an existing speech-recognition tool to estimate sung words and an existing chord-analysis tool to estimate chord changes, and combines their timed results in a report. It compares those estimates with a hand-checked lyric and chord reference.

The audio and inference stay on the learner's computer; the tool does not submit recordings to a hosted API. Model files may need to be downloaded during setup, so their provenance and licenses must be checked. Speech recognition is usually designed for speech, not singing, and chord estimation can be ambiguous in a mixed recording. The first experiment tests those uncertainties and reports results rather than assuming success.

Python is the accepted first-experiment format. A web application, model training, and other instruments can be considered only after this local analysis has been evaluated.

## The Core Journey Through the System

PRD ref: `prd.md > The Core Journey`.

```text
Provide a local piano-and-vocal recording
    ↓
Run the Python analysis command
    ↓
Speech recognizer estimates sung words and times
    ↓
Chord analyzer estimates chord labels and time ranges
    ↓
Combine the predictions on a shared timeline
    ↓
Compare predictions with the hand-checked reference
```

The input path is a local file path. Separate analysis components produce time-stamped lyric and chord predictions; a report layer aligns them and compares them with an authored reference. Predictions and reference data remain distinguishable. No cloud inference, platform URL access, database, or persistent user account is needed.

## Stack

- **Python:** Local command-line experiment, selected by the learner instead of the previously planned Vite website.
- **Sung-word recognition:** Use `faster-whisper` with word timestamps as the first local ASR candidate. It is a speech model, not singing-specific; measure singing performance on the learner's recording. The implementation is MIT-licensed, and the selected `Systran/faster-whisper-base` model card lists MIT; review dependency terms before redistribution.
- **Chord estimation:** Use `librosa` chroma features and a transparent major/minor triad-template matcher as the first baseline. Average chroma over 21 frames, smooth labels over 21 frames, merge runs shorter than 0.4 seconds, and label low-energy frames as `N` (no chord) using a relative RMS floor. This is signal processing, not a trained AI chord model; it gives a checkable starting point before collecting data for model training. `librosa` is ISC-licensed. Seventh and add9 qualities are not represented and will be approximated by triads.
- **Reference comparison:** Store hand-checked word/chord timing in a small local data file and compare it with predictions.
- **Audio decoder compatibility:** Constrain PyAV to versions below 19 for the selected `faster-whisper` release; the installed PyAV 19.0.2 rejected an argument used by its local decoder.
- **No hosted inference or remote runtime service.** Models may be obtained during setup; once installed, processing the recording remains local.

The `faster-whisper` documentation describes local Whisper inference, model download, and word timestamps: [faster-whisper](https://github.com/SYSTRAN/faster-whisper). The selected converted model downloads from Hugging Face, whose model card lists MIT: [faster-whisper base model](https://huggingface.co/Systran/faster-whisper-base). `librosa` provides chroma features for music analysis: [librosa feature documentation](https://librosa.org/doc/latest/feature.html). These tools do not guarantee accurate transcription of singing or chords.

## Where It Runs and How Someone Tries It

- **Runtime:** Local Python command-line experiment on the learner's computer; the current CLI accepts nonempty WAV files only.
- **Language hint:** `--language` optionally passes a language code to Whisper when automatic detection is incorrect; omitting it preserves automatic detection.
- **Requirements:** Python version and supported audio formats depend on the selected candidate libraries; verify these before installing. A model download may require internet during setup. No API key or hosted inference.
- **Try it:** Run `python analyze.py <recording.wav> --language id --output output` for Indonesian vocals (or omit `--language` for automatic detection); inspect the generated local analysis.
- **Input:** Begin with a short WAV recording of the learner's piano-and-vocal performance; expand formats only if needed.
- **Privacy:** Do not upload audio to a service. Keep the recording, transcript, reference, and report local and out of the public repository.

## Look and Feel

The generated report should prioritize legibility and clear comparison. Label predicted and reference lyrics/chords distinctly, show their time ranges, and avoid visual treatment that suggests predictions are verified facts.

## Components

### Local Audio Input

Validates a user-supplied local audio path and reports unsupported or unreadable input clearly.
PRD ref: `prd.md > The Core Journey`, `Features and Behavior > Local Recording Analysis`.

### Sung-Word Recognition

Runs the selected local recognition and alignment tool on the vocal in a piano-and-vocal recording and returns words with timing and confidence information when available. Singing performance must be tested rather than assumed.
PRD ref: `prd.md > Features and Behavior > Sung Words and Chord Estimates`, `States and Boundaries`.

### Chord Estimation

Runs a locally selected chord-analysis tool on the recording and returns chord labels with start/end times. Preserve uncertainty and avoid presenting the output as ground truth.
PRD ref: `prd.md > Features and Behavior > Sung Words and Chord Estimates`.

### Reference Comparison and Report

Combines timed predictions with a hand-checked reference and writes a readable report in a local output directory. Keep source predictions and reference data separate so a comparison cannot overwrite the original output.
PRD ref: `prd.md > The Core Journey`, `Features and Behavior > Sung Words and Chord Estimates`.

## Data Model

- **Input recording:** Local audio path; first test uses a short PCM WAV of the learner's piano-and-vocal performance.
- **Reference annotations** (`data/reference.json`): hand-checked lyric words/segments and chord labels with start/end times for the exact recording; this file stays local and ignored by Git.
- **Analysis output** (`output/analysis.json`): recording metadata, predicted lyric words/timestamps, chord labels/time ranges, tool/version information, and confidence when available.
- **Comparison output** (`output/report.html`): predictions and reference remain separately labeled; comparison results are descriptive for this sample only.
- Do not commit the learner's raw audio, personal voice recording, transcript, reference, or generated report.

## File Structure

```text
Build With AI/
├── pyproject.toml                      # Python package metadata and dependencies
├── analyze.py                          # Local CLI entry point
├── src/cadence/
│   ├── transcription.py                # Sung-word recognition and timing
│   ├── chords.py                        # Chord estimation and timing
│   ├── comparison.py                   # Compare estimates with reference annotations
│   └── report.py                        # Generate a readable local report
├── data/
│   └── reference.example.json          # Schema/example; no personal recording
├── tests/                               # Tests for parsing, alignment, comparison
├── output/                              # Local, private analysis results
└── devpost/                            # Canonical planning documents and review companions
```

## External Services and Dependencies

- **Speech recognition/alignment:** Use `faster-whisper` for local Whisper inference and word timestamps. Confirm the chosen model card/license and dependency terms, then test singing performance.
- **Chord analysis:** `librosa` chroma features with a simple major/minor triad-template baseline; evaluate it against the learner's known progression before extending chord types.
- **Audio decoding:** Add a local decoder only if required; WAV is the initial target.
- **External runtime services:** None. Do not transmit audio or reference annotations to a hosted API.

## Important Failure Modes

- **Sung words are missed or hallucinated** → Show model output as an estimate, retain the reference separately, and report the mismatch; do not substitute reference lyrics as model output.
- **Chord estimates are unstable or ambiguous** → Preserve predicted segments/confidence when available and report poor fit instead of inventing stable chords.
- **Dependency or model license is unsuitable** → Do not add it; pause and evaluate a compatible alternative.
- **Model or audio input is unavailable/unsupported** → Return a clear error and preserve existing local files and references.
- **Installation or local inference exceeds available resources** → Measure this in the first experiment and discuss a scope/architecture revision rather than silently switching to cloud processing.

## What Was Simplified and Why

- One learner-provided piano-and-vocal recording instead of a broad catalog — provides a bounded feasibility test.
- Existing local tools instead of training a model — avoids implying a large labeled training set or high accuracy exists.
- A hand-checked reference alongside predictions — makes errors visible and comparable.
- Python command-line experiment instead of a web app — tests analysis before interface and deployment work.
- Local processing instead of a hosted API — keeps the learner's voice recording on their own device.

## Decisions and Open Issues

- **Learner choice — private piano-and-vocal recording:** The learner will provide their own voice and piano accompaniment; the recording and its analysis stay private.
- **Learner choice — automatic sung-word transcription:** The experiment should recognize words from the vocal recording rather than use supplied lyrics as the prediction.
- **Learner choice — Python experiment:** Use a local Python analysis experiment before deciding whether to build a web app.
- **Learner choice — existing analysis tools:** Start with existing tools, not training a model from scratch.
- **Privacy constraint:** Keep the recording and inference local; do not use a hosted transcription API.
- **Sharing constraint:** Do not publish this recording, its transcript, reference annotations, or generated report.
- **Open build investigation:** Verify local runtime requirements and word-timestamp behavior on the learner's recording; verify `librosa` chroma/template behavior on the learner's piano recording. The selected model card lists MIT, but dependency terms still need review before redistribution.
- **Open measurement:** Agree how to annotate the reference and report word/chord mismatches; one recording cannot establish general accuracy.
- **Observed limitation:** The opening B–E–B–E sequence matches the learner's reference, but the initial baseline incorrectly labeled three learner-identified E-major spans as C#m/A#m/G#m. Preserve these predictions and show the verified E-major reference separately; this sample does not yet establish reliable chord recognition.
- **Future decision:** Revisit a web interface, more instruments, and a training dataset only after this experiment produces measured evidence.
