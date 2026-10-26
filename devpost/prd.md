---
doc: prd
status: approved
---

# Cadence — Product Requirements

Cadence (“Resolve Every Song.”) is an educational chord-progression databank paired with a small chord-learning experiment for musicians.
Source: `scope.md > The Unique Kernel`, `Who It's For`.

## The Core Journey

1. Before the public demo, the project owner trains a chord-label model with original recordings paired with correct chord labels. They check its predictions against reference labels on a different song that was not used for training.
2. The visitor opens Cadence and chooses their music experience. Beginners can take a short major-scale tutorial or skip it.
3. The visitor explores the progression databank, searches or filters its curated patterns, and opens a lesson to hear and understand one.
4. The visitor can choose a local song they are authorized to analyze. Cadence uses the already-trained model; visitors do not need the training examples and do not need to train the model themselves.
5. Cadence shows estimated chord labels and estimates the song's key, tempo, and time signature. The visitor can correct those estimates, enter a song title, and mark or edit verse/chorus/bridge sections.
6. The visitor reviews a bar-by-bar chart, with chord placements on beats and beat markers shown as dots, then exports a printable PDF containing the title, key, time signature, song sections, and chord chart. Estimated results remain visibly uncertain in the app and PDF.
7. If the chord estimates resemble a catalog progression, the visitor can open that lesson. A weak or unmatched estimate remains unlinked.

Cadence demonstrates an educational databank and a small, honest model-training experiment. It does not promise that the model will correctly transcribe unfamiliar songs.

## Screens and Layout

- **Welcome and experience choice:** Ask whether the visitor is new to music or has some experience. Beginners can open or skip the tutorial, then choose the databank or song analysis.
- **Beginner tutorial:** A short, skippable explanation of the major scale and its diatonic chord qualities.
- **Progression databank:** Search and frequency filter above a compact grid of progression cards.
- **Progression lesson:** A selected progression's explanation, relevant theory diagram, chord spellings, and playable example.
- **Song analysis and chart preview:** Local audio selection, chord estimates, estimated key/tempo/time signature, editable song title and section labels, controls to correct musical metadata, and a preview of the bar/beat chart before PDF export.
- **Training and evaluation demonstration:** A project-owner step shown before or during the demo: run training on the prepared, chord-labeled original recordings and show the held-out evaluation. The public app uses the resulting pre-trained model; visitors are not asked to train it.

## Look and Feel

Use warm, pleasing colors with a subtle jazz-club atmosphere, but keep the interface simple and minimal. Small café or instrument details (such as a coffee mug, piano, or cello) may appear as restrained decoration, never competing with the progression grid, diagrams, chord estimates, or printable chart. Warnings about uncertain model output should be clear and plain-spoken. The PDF should prioritize readable chord placement and clean printing over decoration.

## Features and Behavior

### Experience choice and beginner tutorial

Source: `scope.md > The Core Loop`, `The POC Boundary`.

- Ask whether the visitor is new to music or has some experience.
- Beginners can start a short tutorial or skip it and continue to either the databank or song analysis.
- Explain the major scale and diatonic chord qualities I, ii, iii, IV, V, vi, and vii°.
- If it fits the brief explanation, show vii° as a possible V/vii slash-chord substitution; this is supporting context, not an extra lesson.
- The tutorial is educational content, not a test; learner ratings and saved course progress are not required.

**Acceptance criteria**
- [ ] A first-time visitor can choose an experience level and reach the tutorial or skip it.
- [ ] Skipping the tutorial still allows access to both the databank and song-analysis entry point.
- [ ] The tutorial identifies the seven diatonic major-scale chord qualities and distinguishes major, minor, and diminished symbols clearly.

### Searching and browsing the progression databank

Source: `scope.md > The Unique Kernel`, `The Core Loop`, `The POC Boundary`.

- Search progression entries by their name or Roman-numeral pattern.
- Filter by curated frequency group: frequent, medium, or less common.
- Show a compact grid; each card identifies the progression and its frequency group.
- The starter collection focuses on diatonic major-key patterns and excludes the out-of-scale II, III, and v examples.
- Frequency is curated learning guidance, not a statistically measured ranking across all online songs.
- Seed examples include:
  - **Frequent:** I–vi–IV–V, vi–IV–I–V, I–IV–V–I, ii–V–I.
  - **Medium:** I–V–vi–IV, I–vi–ii–V.
  - **Less common:** additional diatonic progressions selected for the small starter collection.
- Search or filter with no matching entry shows a clear empty state and lets the visitor adjust the query or filter.

**Acceptance criteria**
- [ ] Searching by a progression name or Roman-numeral sequence can find the matching entry.
- [ ] Selecting a frequency group limits the visible cards to that group; clearing the filter restores all entries.
- [ ] Every card shows a progression name, Roman-numeral sequence, and frequency group.
- [ ] The starter set contains the learner-ranked examples, and any less-common entries stay diatonic.
- [ ] A query with no match displays an explicit “no progressions found” state rather than a blank grid.

### Understanding and hearing a progression

Source: `scope.md > The Unique Kernel`, `The Core Loop`, `What "Working" Looks Like`.

- Opening a card shows the progression name and Roman-numeral sequence, its curated frequency group, a concise explanation of how it is derived or applied, a relevant theory diagram when useful, and an audio example.
- The explanation connects chord movement to the major scale and, where relevant, the circle of fourths/fifths or another useful theory idea.
- For ii–V–I, the explanation may show roots moving by fourths (equivalently, fifths in the opposite direction) and explain how landing on I gives a sense of resolution.
- The audio example can be played and stopped; transposition or modulation is not needed.
- Real-song examples are not required for the first version.

**Acceptance criteria**
- [ ] Opening a card reveals its explanation and diagram, if provided, without losing the ability to return to the grid.
- [ ] Each starter entry has a playable audio example that illustrates its progression.
- [ ] Explanations describe a meaningful relationship behind each pattern rather than only restating its chord symbols.
- [ ] Audio playback failure is explained, and the written progression and lesson remain usable.

### Training and evaluating the chord model

Source: `scope.md > The Unique Kernel`, `The Core Loop`, `What "Working" Looks Like`, `The POC Boundary`.

- The project owner trains a chord-label model using the learner's original recordings paired with correct chord labels and approximate bar or time boundaries.
- Simplify charted seventh/sixth chords to their same-root major or minor triads, and ignore the bass inversion on slash chords. Keep observed augmented triads (Daug and Eaug) as distinct labels. They appear only in Demo 5, so that song must remain in training and the demo must disclose that augmented chords have no independent held-out evaluation.
- Training is a project-owner/demo step, not a required visitor action. The public app loads the resulting pre-trained model.
- The training run is reproducible and can be shown in the demo. The output makes it clear that training completed and which labeled examples were used.
- On a song kept entirely out of training, compare the trained model and the existing non-trained chord-template analyzer against the correct labels. Report the measured difference without promising that training will improve accuracy. If the dataset is too small for a meaningful song-level holdout, disclose that limitation.
- Show model outputs as estimates, not verified transcriptions. Training on the learner's songs does not guarantee accuracy on unfamiliar recordings.
- Original full-band recordings are allowed; instrument separation is not required.

**Acceptance criteria**
- [ ] The learner's prepared recordings and chord labels can be used to train the model.
- [ ] A training run produces a model usable by the app and a clear indication that training completed.
- [ ] The demo compares the trained model and the existing analyzer against reference labels on music excluded from training, or clearly reports why the dataset is too small for a meaningful comparison.
- [ ] Visitors can use the pre-trained model without supplying training data or starting a training run.
- [ ] Model results are visibly labeled as experimental estimates.

### Analyzing a local song

Source: `scope.md > The Core Loop`, `What "Working" Looks Like`, `The POC Boundary`.

- The visitor chooses a local audio file they are authorized to analyze. The app does not accept streaming links or download music.
- Complete songs and full-band recordings are allowed; instrument separation is not required.
- Use the pre-trained model to show estimated chord labels and spans. Also estimate key, tempo, and time signature for the chart.
- Label these estimates clearly and let the visitor correct key, tempo, and time signature before making the chart.
- The visitor supplies the song title and can mark or edit section names such as verse, chorus, and bridge. Cadence does not automatically identify song sections in this POC.
- A plausible progression match can link to the corresponding databank lesson. When no catalog pattern matches, keep the chord estimates visible without highlighting an unrelated entry.
- An unreadable, unsupported, or failed analysis shows an actionable error, not fabricated results.

**Acceptance criteria**
- [ ] A local audio file can be selected without entering a streaming URL.
- [ ] The result view visibly labels chord, key, tempo, and time-signature output as estimates.
- [ ] The visitor can correct the key, tempo, and time signature and enter a song title before export.
- [ ] The visitor can add or edit section labels; the app does not claim to detect verse/chorus structure automatically.
- [ ] A recognized progression links to its corresponding databank lesson; an unmatched estimate has no misleading lesson link.
- [ ] An unsupported or unreadable file produces a clear error and no success-shaped result.
- [ ] The app reminds visitors to use audio they are authorized to analyze.

### Exporting a performance chart

Source: `scope.md > The Core Loop`, `What "Working" Looks Like`, `The POC Boundary`.

- From the song-analysis result, the visitor can export a printable PDF chart.
- The PDF includes the user-supplied song title, key, time signature, song section labels, numbered bars, and estimated chord placements across beats. Beat positions can be shown as dots.
- Use corrected key, tempo, and time-signature values in the chart. Include tempo with the chart metadata because it determines bar alignment.
- Keep chord estimates visibly identified as estimates in the PDF, so the chart is not mistaken for verified sheet music.
- Arrange longer songs across as many readable pages as needed; the PDF is for performance reference, not formal notation.

**Acceptance criteria**
- [ ] A visitor can create and open or download a PDF from an analyzed song.
- [ ] The printout shows title, key, time signature, tempo, song sections, bar numbers, beat markers, and chord labels in a readable layout.
- [ ] The chart reflects user-corrected metadata and manually edited section labels.
- [ ] The PDF clearly notes that chord content is an estimate.
- [ ] If the PDF cannot be generated, explain the failure and leave the on-screen analysis available.

## States and Boundaries

- **First visit:** Experience choice appears; beginners can launch or skip the tutorial.
- **Empty search:** Explain that no progression matched and allow search/filter changes.
- **Uncertain analysis:** Show the experimental-estimate warning in the app and exported chart.
- **Uncertain metadata:** Mark key, tempo, and time signature as estimates and allow correction before export.
- **No progression match:** Keep chord estimates visible but do not highlight an unrelated databank entry.
- **Missing title or section labels:** Prompt the visitor to provide a title; section labels may be left blank or edited before export.
- **Analysis or PDF error:** Explain the failure and do not display fabricated results; retain any valid on-screen analysis if only export failed.
- **Rights and privacy:** Analyze only local audio the visitor is authorized to use. The app processes visitor audio locally and does not store or share it. The learner confirmed their original training recordings and performances may be included in the public demo/repository.
- **Frequency boundary:** Frequency groups are curated guidance, not measured claims about all songs.
- **Persistence:** No account, ratings, or saved learning history in this POC. Visitor uploads and results are temporary.

## Product Decisions

- Keep **Cadence** and the tagline **“Resolve Every Song.”**
- Keep the educational progression databank as the main differentiator and add a small chord-label training experiment using the learner's original, chord-labeled recordings.
- Train the model before visitor use; show the training and held-out evaluation in the demo, then let visitors use the pre-trained model without training.
- Compare the trained model with the existing chord-template analyzer on the same held-out song to check whether training helped; report the result honestly.
- Derive progression candidates from chord predictions rather than training a second progression model.
- Let visitors analyze authorized local audio, including full-band recordings, while clearly labeling model outputs as experimental.
- Estimate key, tempo, and time signature in the app and allow visitors to correct those values. Visitors supply the song title and mark or edit song sections.
- Include a printable PDF performance chart with chord positions by bar/beat; do not build automatic song-section detection.
- Use the learner's ranked starter groups: frequent (I–vi–IV–V, vi–IV–I–V, I–IV–V–I, ii–V–I), medium (I–V–vi–IV, I–vi–ii–V), plus some less-common diatonic examples.
- Explain frequency groups as curated learning guidance, not a survey.
- Focus the beginner path on the major scale and diatonic chord qualities; keep II, III, and v out of the starter set.
- Use a warm, minimal jazz-club visual mood with restrained decorative details.

## What We're Building

- Welcome experience choice and a short optional major-scale primer.
- A small searchable/filterable databank of diatonic major-key progressions with lessons and synthetic audio.
- A reproducible training run and held-out evaluation for a chord-label model trained from the learner's labeled original recordings.
- Local analysis of visitor-provided audio using the pre-trained model, with estimated and editable key/tempo/time-signature details.
- A bar/beat chord chart with user-provided title and section labels, exportable as a printable PDF.
- Optional links from plausible progression estimates to a databank lesson.
- Clear uncertainty notices, error states, local-only visitor audio processing, and rights-respecting input boundaries.

## Deferred From the POC

- Automatic verse/chorus/bridge detection: users mark or edit these labels; automatic music-structure recognition is a separate modeling task.
- Automatic reading of chord-chart PDFs into training labels: the training examples must already include chord labels aligned to approximate bars or times.
- Instrument separation, lyrics, tabs, formal notation, and guaranteed transcription of arbitrary recordings.
- Additional training data, genres, keys, chord types, and model optimization beyond the small proof of concept.
- A sourced, statistically representative progression-frequency survey.
- Saved ratings, user accounts, song history, streaming links, hosted analysis, and deployment.

## Possible Later Enhancements

- Expand the training set and evaluate across more independent songs, styles, instruments, and chord qualities.
- Explore automatic song-structure detection or chart-PDF ingestion if users need them.
- Add additional keys, minor-key lessons, and richer theory relationships.
- Revisit frequency groups using a documented, properly licensed corpus and counting method.

## Non-Goals

- Claiming the chord model reliably recognizes arbitrary songs.
- Requiring visitors to train the model or provide the learner's training examples.
- Automatically detecting song sections, producing lyrics/tabs, or exporting formal notation.
- Accepting streaming URLs, downloading platform music, or sending visitor audio to a hosted service.
- Claiming curated frequency groups are objective, internet-wide statistics.

## Open Questions

- Which exact less-common diatonic patterns should seed the starter collection? Can be finalized while preparing lesson content.
- Which chord-label vocabulary and local audio formats can the model support reliably? Settle the bounded label set and WAV/MP3 behavior in `4-spec` before implementation.
- What training-label file format is simplest for the learner to prepare from their annotated recordings? Decide in `4-spec`; automatic PDF reading is deferred.
