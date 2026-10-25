---
doc: checklist
status: approved
---

# Build Checklist

Build mode: learn

## Slices

- [ ] **1. A recording yields timed lyric and chord estimates**
  Becomes usable: A local Python command analyzes one private piano-and-vocal recording and writes estimated sung words and chord changes with timestamps to a structured output file.
  Why now: Bootstrapping is part of the first usable step, and this tests the two central risks—recognizing singing and estimating chords from a mixed recording—before investing in a larger product.
  PRD ref: `prd.md > The Core Journey`; `prd.md > Features and Behavior > Local Recording Analysis`; `prd.md > Features and Behavior > Sung Words and Chord Estimates`
  Spec ref: `spec.md > Stack`; `spec.md > Where It Runs and How Someone Tries It`; `spec.md > Components > Sung-Word Recognition`; `spec.md > Components > Chord Estimation`; `spec.md > File Structure`
  Build: Bootstrap the Python CLI; confirm the selected Whisper model card's MIT license and local runtime requirements; use faster-whisper for word-timed sung-word estimates and librosa chroma features with a major/minor triad-template baseline for chord estimates. Allow an optional language hint when auto-detection is wrong. Analyze the learner's PCM WAV recording and write timestamped JSON predictions locally. Keep the hand-checked reference out of model input and use it only for later evaluation.
  Verify (mechanical): Run `python -m unittest discover -s tests` and `python analyze.py <recording.wav> --language id --output output` when Indonesian is sung; confirm `output/analysis.json` contains timed word and chord predictions, then compare them with the separately supplied reference and record observed misses. Do not claim general accuracy from this sample.
  Learner check: Review the generated words and chord intervals alongside your reference. Point out one place the tool got right and one place it missed or was uncertain.
  Commit: `Analyze private piano-vocal recording`

- [ ] **2. You can inspect estimates against your reference**
  Becomes usable: A generated local report places the estimated words and chord changes alongside the hand-checked reference on a shared timeline and summarizes mismatches.
  Why now: Raw machine output is hard to judge; a comparison report makes the experiment's accuracy and limitations visible without treating predictions as verified truth.
  PRD ref: `prd.md > The Core Journey`; `prd.md > Features and Behavior > Sung Words and Chord Estimates`
  Spec ref: `spec.md > Components > Reference Comparison and Report`; `spec.md > Data Model`; `spec.md > Important Failure Modes`
  Build: Add a reference-annotation format, time-alignment/comparison logic, and a readable report that clearly distinguishes predictions from reference data.
  Verify (mechanical): Run `python -m unittest discover -s tests` and `python analyze.py <recording.wav> --reference data/reference.json --output output`; verify comparison results against a hand-checked fixture with known matching and mismatching words/chord intervals, then generate and inspect the report for the learner's recording.
  Learner check: Open the report, follow one lyric/chord region on the timeline, and tell me whether it makes the model's success and mistakes easy to understand.
  Commit: `Compare analysis with verified reference`

## Hands-on Checkpoints

- [ ] Early usable behavior explored — after Slice 1, inspect the estimated words/chords against your reference and report how well the analysis works on your recording.
- [ ] Final kick-the-tires exploration and feedback completed — after Slice 2, inspect the full report, try awkward or unclear regions, and report anything confusing or worth changing.

## Final Review

- [ ] Final review complete — feedback resolved and learner confirms the experiment is ready to share

## Code Tour and App Map

- [ ] Learning activity complete — connect the team's learning goal to one analysis step, its implementation, and verification evidence
- [ ] Optional edit and transfer reflection addressed — offered/declined/already covered/not applicable as appropriate
- [ ] `devpost/app-map.html` generated from finished code, checked, and shown, including a project-grounded practice to reuse

Activity and evidence: Not started.
Route and stops: Not started.
Edit outcome: Not started.
Reflection: Not started.
Activity mode: Not started.

## Revisions

- Replaced the prepared-song Vite website build with a local Python feasibility experiment for the learner's piano-and-vocal recording; the learner chose automatic sung-word transcription, piano accompaniment, Python, and existing analysis tools. Comparison against a hand-checked reference is included; training and broader accuracy claims are deferred.
- Narrowed the first local tool candidates to faster-whisper for speech recognition and librosa chroma features for a transparent chord baseline after checking their project licenses; the selected faster-whisper model card lists MIT. Results on singing and the learner's recording remain to be verified. The chord baseline is signal processing, not a trained chord AI model.
- The CLI accepts nonempty WAV files and writes `analysis.json` inside the `--output` directory; align the learner instructions with those actual interfaces.
- The installed PyAV 19.0.2 rejected a decoder keyword used by faster-whisper 1.2.1; constrain PyAV to `<19` and verify local decoding.
- The first real recording run auto-detected the wrong language and produced 887 short chord intervals. Added an optional language hint after the learner identified Indonesian; chord stability still needs evaluation against their reference before this slice can pass.
- The attached chord chart includes add9 and minor-7 qualities that the current major/minor triad templates cannot express, and it has no timestamps. The first output had 634 of 887 intervals shorter than 0.25 seconds, so it is not a reliable chord result yet.
- Added temporal chroma averaging, longer label smoothing, and a 0.4-second minimum chord run after the unstable real-recording result. The chord output fell from 887 to 183 intervals, with 16 shorter than 0.4 seconds; a synthetic C-major triad still produces one C interval at 0.99 template score. Learner review against the chart is still required.
- The learner confirmed the opening 0.0–1.1 seconds should have no chord, while the following B–E–B–E sequence is correct. Inspection found digital silence at the start, but chroma-template noise still yielded G#m/A#m; added a relative RMS energy gate to label low-energy frames `N` and retest the opening.
- The learner identified additional false positives: 11.56–12.09s should remain E; 14.16–15.67s and 19.89–20.89s should be E major, not the estimated C#m/A#m/G#m labels. The learner also corrected one recognized word at 29.76–32.52s. Keep these corrections in the private reference, not in model predictions; the report should make the baseline's melody-versus-harmony limitation visible.
- The recording is a private learner-provided performance, not an original composition. Keep its audio, transcript, reference, and report local; do not use them in a public demo or submission.
