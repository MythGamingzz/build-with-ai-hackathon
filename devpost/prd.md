---
doc: prd
status: approved
---

# Cadence — Product Requirements

Cadence (“Resolve Every Song.”) is a local experiment that estimates chords and transcribes sung words from one learner-provided piano-and-vocal recording.
Source: `scope.md > The Unique Kernel`, `Who It's For`.

## The Core Journey

1. The musician provides a short piano-and-vocal recording and prepares a hand-checked reference containing the intended lyrics and chord changes.
2. They run the local Python analysis tool on the recording.
3. The tool estimates sung words and their timings, and estimates chord labels and their time ranges.
4. The tool writes a report that aligns the estimates on a shared timeline and compares them with the hand-checked reference.
5. The musician inspects the report and identifies where the estimates match or miss the reference.

The proof is demonstrable when the local tool produces time-stamped lyric and chord estimates for the supplied recording and makes their differences from the reference inspectable. One song is an experiment, not evidence of broad accuracy.

## Screens and Layout

- **Local analysis report:** A simple generated report with the estimated lyric words and chord intervals on a shared time axis, alongside the hand-checked reference. Keep predicted and reference values visually distinct.
- **Command-line input:** The musician supplies the path to a local audio recording; no web account or hosted service is involved.

## Look and Feel

Prioritize a readable, honest analysis report over visual polish. Clearly label software estimates, reference annotations, and uncertainty; do not imply the output is verified ground truth.

## Features and Behavior

### Local Recording Analysis

Source: `scope.md > The Core Loop`, `The POC Boundary`.

- The musician provides a nonempty PCM WAV file containing one short performance with piano and sung vocal.
- Analysis runs locally; the recording is not sent to a hosted service.
- The tool uses existing locally runnable analysis software rather than training a new model for this prototype.
- The musician can provide an optional language hint when automatic detection is incorrect.

**Acceptance criteria**
- [ ] The musician can run the analysis on the specified local recording.
- [ ] An unsupported, missing, or unreadable file produces a clear error and does not silently return success-shaped output.
- [ ] The tool does not fetch audio from a URL or transmit the recording to a remote service.
- [ ] A malformed reference or one for a different recording produces a clear error before analysis begins.

### Sung Words and Chord Estimates

Source: `scope.md > The Core Loop`, `What "Working" Looks Like`.

- The tool estimates sung words and their times, plus chord labels and time ranges.
- It aligns both estimates on one shared timeline; chord estimates remain distinct from manually verified reference labels.
- A hand-checked reference for the recording supplies the intended lyrics and chord changes for comparison.
- The generated report shows estimated values next to the reference so mismatches can be inspected.

**Acceptance criteria**
- [ ] The analysis output contains time-stamped lyric segments and time-ranged chord estimates.
- [ ] The report places both on a shared timeline and clearly separates predictions from reference annotations.
- [ ] The report makes comparison possible without claiming a high-accuracy result from one recording.
- [ ] If a selected tool cannot reasonably transcribe sung vocals or estimate chords from this recording, the limitation is reported rather than hidden.

## States and Boundaries

- **Input boundary:** One short local piano-and-vocal PCM WAV recording. No YouTube/Spotify links or remote audio fetching.
- **Privacy boundary:** Audio analysis runs locally; do not upload the user's recording to a remote service.
- **Sharing boundary:** Keep this recording, transcript, reference, and generated report private; do not use them in a public demo or submission.
- **Analysis boundary:** Output is an estimate. A single recording does not establish performance on other songs, instruments, voices, or recording conditions.
- **Reference boundary:** Comparison uses a hand-checked lyric and chord reference supplied for the same recording.
- **Failure:** Missing models, unsupported audio, and analysis failures must be reported explicitly; never produce blank or fabricated success output.

## Product Decisions

- Use the name **Cadence** and tagline **“Resolve Every Song.”**
- Use one piano-and-vocal recording supplied by the learner and keep its analysis private.
- Run a local Python analysis experiment; do not build the Vite website in this first prototype.
- Use existing analysis tools, subject to verifying their singing performance, compatibility, and licenses; do not train a model from scratch.
- Compare estimated words and chords against a hand-checked reference and report observed limitations.
- Keep additional instruments, songs, hosted inference, URL ingestion, and a polished application outside this POC.

## What We're Building

- A command-line Python tool for one local audio recording.
- Time-stamped estimates of sung words and chord changes.
- A generated report that aligns predictions and compares them with hand-checked reference data.
- Explicit errors and honest reporting of the experiment's limitations.

## Deferred From the POC

- A browser interface, hosted deployment, and general user-facing upload workflow.
- URL input, including YouTube or Spotify, and remote downloading.
- Multiple songs, guitar/bass/drums, arbitrary instruments, and broad accuracy claims.
- Training or fine-tuning a new model.

## Possible Later Enhancements

- Test more original or appropriately licensed recordings and instruments.
- Explore model training or fine-tuning with a sufficiently large, properly licensed, hand-labeled dataset.
- Build a web application after local analysis feasibility is demonstrated.
- Add instrument-specific analysis or music-learning features if later scope supports them.

## Non-Goals

- Claiming the experiment accurately transcribes arbitrary music.
- Downloading or analyzing songs from platforms without an authorized access method and applicable permission.
- Training a model from scratch or treating one recording as a representative dataset.

## Open Questions

- Which locally runnable chord-analysis tool can produce useful time-ranged estimates for piano-and-vocal audio under a suitable license?
- How accurately can an existing speech-recognition tool transcribe sung words and align them in this recording?
