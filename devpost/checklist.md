---
doc: checklist
status: approved
---

# Build Checklist

Build mode: fast

## Slices

- [x] **1. Train and evaluate a chord model**
  Becomes usable: The project owner can run one local command that trains a chord-label model from four original songs, compares it with the existing template analyzer on a fifth song held out in full, reports measured accuracy and macro-F1 with limitations, and saves a model the app can load.
  Why now: This is the highest-risk part of the distinctive model experiment. Proving the data, training, and honest evaluation path first gives the rest of the build a real saved model to use rather than a placeholder.
  PRD ref: `prd.md > The Core Journey`; `prd.md > Training and evaluating the chord model`; `prd.md > States and Boundaries`
  Spec ref: `spec.md > Stack`; `spec.md > Where It Runs and How Someone Tries It`; `spec.md > Components > Shared Audio Features and Existing Baseline`; `spec.md > Components > Training and Held-Out Evaluation`; `spec.md > Components > Tests`; `spec.md > Data Model`; `spec.md > File Structure`; `spec.md > Important Failure Modes`
  Build: Use the five learner-owned original recordings and their chord references (not the earlier copyrighted cover); keep Demo 5 in training because it is the only source of Daug/Eaug, and hold Demo 3 out as a complete song. Check file sizes, audio decoding, annotation coverage, interval validity, and supported chord labels. Simplify seventh/sixth chords to same-root major/minor triads, ignore slash-chord bass inversions, and preserve Daug/Eaug as their own labels. Add the training dependencies, timed-annotation validation, shared chroma features, song-level split, logistic-regression training, same-frame baseline comparison, clear metrics/limitations, and saved `models/chord_classifier.joblib`. Report that Daug/Eaug are represented by one song and cannot be evaluated on an independent held-out song. Do not save a success-shaped model when the inputs are invalid.
  Verify (mechanical): Run `.venv\Scripts\python.exe -m unittest discover -s tests` and `.venv\Scripts\python.exe -m cadence.training`; confirm split tests keep songs separate, chart-label normalization preserves Daug/Eaug while simplifying extensions/inversions, the command prints both methods' measured accuracy and macro-F1 plus unsupported-label limits, the report discloses that augmented labels have no held-out evaluation, and the saved artifact loads successfully. MP3 decoding has been verified for all five supplied recordings.
  Learner check: Provide the five original tracks and chord references, review the timed labels and held-out song assignment, run the training command, and check that its output clearly shows what it learned and how the held-out comparison turned out.
  Commit: `Train and evaluate chord classifier`

- [x] **2. Explore and learn from a progression**
  Becomes usable: A visitor can open the local browser app, take or skip the paced keyboard-and-scale primer, search and filter the curated diatonic and selected non-diatonic progressions, open a lesson with a circle-of-fifths diagram and correct spellings in all 12 keys, and play its quieter, more spacious piano-like synthetic audio example.
  Why now: The databank is Cadence's educational core. Once the model-training risk is proven, this is the first complete visitor-facing experience and creates the lesson catalog that song estimates can later link to.
  PRD ref: `prd.md > The Core Journey`; `prd.md > Experience choice and beginner tutorial`; `prd.md > Searching and browsing the progression databank`; `prd.md > Understanding and hearing a progression`; `prd.md > Look and Feel`
  Spec ref: `spec.md > Stack`; `spec.md > Where It Runs and How Someone Tries It`; `spec.md > Look and Feel`; `spec.md > Components > Streamlit App and Experience Choice`; `spec.md > Components > Beginner Scale Tutorial`; `spec.md > Components > Progression Data and Databank`; `spec.md > Components > Scale and Key Theory`; `spec.md > Components > Progression Lesson and Diagrams`; `spec.md > Components > Synthetic Audio Examples`; `spec.md > Data Model`; `spec.md > File Structure`
  Build: Add the Streamlit app within the existing Python project; implement experience choice, the seven-step optional tutorial with keyboard/scale visuals and separate chord-table/fifths/fourths lessons, curated diatonic progressions plus I–III–vi, I–III–IV, v–I–IV, and I–II–IV, ordered frequency groups with green/yellow/red labels, lesson explanations and circle diagrams, correct chord spellings across all keys, and quieter/spaced piano-like locally generated WAV examples. Keep frequency groups identified as curated guidance and preserve the existing private CLI experiment.
  Verify (mechanical): Run `.venv\Scripts\python.exe -m unittest discover -s tests`; start `.venv\Scripts\python.exe -m streamlit run app.py` and confirm it responds at `http://localhost:8501`; verify tutorial ordering and controls, separate circle/table views, all-key chromatic chord spellings, progression validation and ordering, and generated WAV level/timing/decay coverage.
  Learner check: Open the app, choose beginner, check that W–W–H–W–W–W–H comes before the scales, compare the two piano diagrams and C/D scale displays, inspect the separate chord table and circles, and use Back/Next and the final finish action. Confirm the home screen has no redundant skip-to-library action but still offers the library. Then search for I–III–vi, confirm it is in the less-common group, open its lesson, inspect the circle diagram and chord spellings in different keys, and play the example. Tell me what feels clear or confusing.
  Commit: `Build searchable progression learning databank`

- [x] **3. Analyze a local song and review its estimates**
  Becomes usable: A visitor can select an authorized local WAV or MP3, see chord predictions from the saved model alongside uncertain key, tempo, and meter suggestions, correct those details, enter a title and section ranges, and open only a plausible progression lesson match.
  Why now: The model and lesson catalog now exist, so this connects the training experiment to the educational kernel. It also tests local audio decoding and the uncertain metadata path before PDF layout depends on it.
  PRD ref: `prd.md > The Core Journey`; `prd.md > Analyzing a local song`; `prd.md > States and Boundaries`
  Spec ref: `spec.md > Where It Runs and How Someone Tries It`; `spec.md > Components > Shared Audio Features and Existing Baseline`; `spec.md > Components > Pre-Trained Chord Inference`; `spec.md > Components > Song Metadata and Bar/Beat Alignment`; `spec.md > Components > Key-Independent Pattern Matching`; `spec.md > Components > Tests`; `spec.md > Important Failure Modes`
  Build: Load only the project's trusted saved model; process selected local audio temporarily; show experimental chord events and estimated key/tempo/time signature with correction controls; let the visitor enter a title and edit section names/bar ranges; align chord events to confirmed bars/beats; match plausible progression patterns in all 12 major keys without forcing a weak match. Explain unsupported files, missing models, and decoding failures; clean up temporary audio.
  Verify (mechanical): Run `.venv\Scripts\python.exe -m unittest discover -s tests`; test model loading and chord-event timing, metadata estimates and corrections, bar alignment, known/ambiguous/no-match patterns, malformed/unsupported files, and temporary-file cleanup. Run the app with an authorized local recording and confirm errors do not produce fabricated results.
  Learner check: Analyze an original or otherwise authorized local recording, inspect the uncertainty notices, correct the suggested key/tempo/meter, add a title and section labels, and check that a lesson opens only for a plausible match.
  Commit: `Add local song chord analysis`

- [x] **4. Export a printable performance chart**
  Becomes usable: A visitor can update a section-aware bar/beat preview, see unique progression matches highlighted and linked to lessons, then download a readable PDF from that confirmed preview.
  Why now: The PDF depends on stable analysis, corrected metadata, and manually entered sections. Building it last avoids polishing a chart before its inputs and bar/beat alignment are verified.
  PRD ref: `prd.md > The Core Journey`; `prd.md > Exporting a performance chart`; `prd.md > States and Boundaries`
  Spec ref: `spec.md > Look and Feel`; `spec.md > Components > Song Metadata and Bar/Beat Alignment`; `spec.md > Components > Key-Independent Pattern Matching`; `spec.md > Components > Chart Data and Section Preview`; `spec.md > Components > Performance Chart PDF`; `spec.md > Components > Tests`; `spec.md > Important Failure Modes`
  Build: Build one validated chart-data model from corrected metadata and section ranges; show its section-grouped bar preview with one amber boundary per measure, dots for `N`/empty beats, and bar 1 anchored at the first predicted chord; require **Update chart preview** after edits to refresh bar assignments and section-specific progression highlights; show a clickable lesson link in the hover detail on uniquely matched chords; generate an in-memory multi-page PDF in the same bar format from that updated data; preserve the preview if PDF generation fails.
  Verify (mechanical): Run `.venv\Scripts\python.exe -m unittest discover -s tests`; test section grouping, beat positions, overlap/invalid-range errors, unique/ambiguous/no-match highlights, and stale-preview gating; verify PDF bytes, fields, multi-page layout, and export-error handling. Run the local demo through preview update and PDF download.
  Learner check: Analyze an authorized recording, enter a title, correct metadata, add distinct section ranges, click **Update chart preview**, and inspect the single amber bar boundaries, first chord at bar 1 beat 1, dots, and hover lesson links on unique matches. Change a section, confirm the preview is marked stale, update it, then download and inspect the same bar format and no-chord intro note in the PDF.
  Commit: `Export printable chord chart PDF`

## Hands-on Checkpoints

- [x] Early usable behavior explored — after Slice 2, try the step-by-step tutorial, search/filter, lesson diagrams, all-key chord spellings, and quieter/spaced synthetic audio; report what is clear or confusing while the analysis and chart work can still benefit from feedback.
- [x] Core journey explored — after Slice 3, run the trained-model analysis flow, correct estimates, add sections, and report any confusing parts before PDF export is finalized.
- [ ] Final kick-the-tires exploration and feedback completed — after Slice 4, explore the complete demo, try an awkward search and an uncertain/no-match result, export a chart, and report anything broken or worth changing.

## Final Review

- [ ] Remove the duplicate white bar glyphs, render all `N` spans as dots, anchor bar 1 at the first predicted chord (excluding any earlier intro), and add clickable progression details on hover; verify the preview and PDF stay consistent.
- [ ] Final review complete — feedback resolved and learner confirms the prototype is ready to share using only rights-cleared demo audio

## Code Tour and App Map

- [ ] Learning activity complete — connect the team's learning goal to one product behavior, its implementation, and verification evidence
- [ ] Optional edit and transfer reflection addressed — offered/declined/already covered/not applicable as appropriate
- [ ] `devpost/app-map.html` regenerated from finished code, checked, and shown, including a project-grounded practice to reuse

Activity and evidence: Not started.
Route and stops: Not started.
Edit outcome: Not started.
Reflection: Not started.
Activity mode: Not started.

## Revisions

- Included Daug and Eaug as distinct chord labels and recorded chart simplification rules — the learner chose to retain augmented triads, while Demo 5 is their only source; keep that song in training and disclose that cross-song performance cannot be evaluated.
- Reopened the diatonic-only library boundary at the learner's request — add I–III–vi, I–III–IV, v–I–IV, and I–II–IV as curated less-common examples, while keeping every diatonic pattern in frequent or medium; teach the changed chord quality rather than presenting these as ordinary diatonic chords.
- Revised the tutorial and audio after hands-on review — introduce the scale formula before scale diagrams, show unhighlighted and full-gold C-major keyboard diagrams, explain the purpose of each separate circle, separate the chord table and circle lessons, remove redundant skip actions, and use a piano-like synthetic envelope without adding recorded or licensed assets.
- Verified and corrected the supplied audio/chart references — all five MP3s decode locally; `Solo_Demo_1.mp3` is the intended Demo 1 audio; Demo 3's first numbered bar starts around 00:00:12; Demo 4 bar 123 is F major and its corrected ending is bars 147–149. Treat bar-derived times as approximate and review alignment against audio before training.
- Selected Demo 3 as the whole-song holdout after confirming Demo 5 must remain in training for the augmented labels — any held-out label absent from the four training songs will be reported and counted as an evaluation miss.
- Corrected Demo 2 bars 1–8 per learner clarification: G is labeled only on beat 1 of bars 1 and 5, with the remaining time labeled `N` (no chord); added a regression test for these intervals.
- Applied matching temporal smoothing, short-run merging, and low-energy masking to both methods before scoring. After reviewing the low held-out result and training-only cross-validation, the learner chose to continue with the honest experiment rather than require a 75% target; do not claim the trained model outperforms the baseline.
- Slice 3 hands-on review — the learner liked the analyzer and requested a section-aware bar-format preview, highlighted lesson links for matched progressions, an explicit update action after section edits, and PDF download after preview; carry these refinements into Slice 4.
- Refined Slice 4 from hands-on feedback — use one section-aware chart model for a refreshable bar/beat preview, per-section progression highlights and lesson links, and the downloadable PDF; prevent stale previews from being exported.
- Final review feedback — replace the table preview with pipe-delimited bar notation, use dots for empty beats, and remove beat numbers beside chord names; keep measure numbers in a separate label above each bar.
- Final review follow-up — remove duplicate bar glyphs, display no-chord events as dots, anchor the chart at the first predicted chord, and link unique progression details from the chord hover.
