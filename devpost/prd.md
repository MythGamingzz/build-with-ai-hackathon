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
6. The visitor can open chord-edit mode directly from the bar preview and type a chord symbol into any beat cell, including an empty one. `N` and `.` mean no chord. Clicking **Done editing** validates and immediately applies the beat changes, recalculates progression matches, and refreshes the chart; a misplaced chord can be moved by clearing its old beat and entering it in the intended beat. Updated chart and PDF output use the corrected cells, which remain visibly distinguished from model estimates.
7. The visitor reviews the corrected bar-by-bar chart, with chord placements on beats and beat markers shown as dots, then exports a printable PDF containing the title, key, time signature, song sections, and chord chart. Estimated results remain visibly uncertain in the app and PDF.
8. If the chord estimates resemble a catalog progression, the highlighted chord itself links to that lesson. A weak or unmatched estimate remains unlinked. With a separate explicit rights confirmation, the visitor may save the recording and corrected intervals locally for owner review and a later manual training run.

Cadence demonstrates an educational databank and a small, honest model-training experiment. It does not promise that the model will correctly transcribe unfamiliar songs.

## Screens and Layout

- **Welcome and experience choice:** Ask whether the visitor is new to music or has some experience. Beginners can open or skip the tutorial, then choose the databank or song analysis.
- **Beginner tutorial:** A skippable, step-by-step primer: introduce W–W–H–W–W–W–H before showing scales; compare unhighlighted piano keys with C-major highlights; compare C major and D major; show the seven diatonic chord qualities; then teach the circles of fifths and fourths in separate steps. Visitors can move forward or back. The final step has one clear finish action rather than a skip action.
- **Progression databank:** Search and frequency filter above a compact grid of progression cards.
- **Progression lesson:** A selected progression's explanation, relevant theory diagram, chord spellings, and playable example.
- **Song analysis and chart preview:** Local audio selection, chord estimates, estimated key/tempo/time signature, editable song title and section labels, controls to correct musical metadata and chord labels directly in the bar/beat chart, and a preview before PDF export. A clearly separate, explicit action saves rights-cleared audio and corrected intervals locally for later owner review; it does not retrain the model.
- **Training and evaluation demonstration:** A project-owner step shown before or during the demo: run training on the prepared, chord-labeled original recordings and show the held-out evaluation. The public app uses the resulting pre-trained model; visitors are not asked to train it.

## Look and Feel

Use warm, pleasing colors with a subtle jazz-club atmosphere, but keep the interface simple and minimal. Small café or instrument details (such as a coffee mug, piano, or cello) may appear as restrained decoration, never competing with the progression grid, diagrams, chord estimates, or printable chart. Warnings about uncertain model output should be clear and plain-spoken. The PDF should prioritize readable chord placement and clean printing over decoration.

## Features and Behavior

### Experience choice and beginner tutorial

Source: `scope.md > The Core Loop`, `The POC Boundary`.

- Ask whether the visitor is new to music or has some experience.
- Beginners can start a short tutorial or skip it and continue to either the databank or song analysis.
- Present the tutorial as paced screens with Next/Back navigation and a skip option before the last step. Begin with a welcoming animated hello, introduce the W–W–H–W–W–W–H formula before showing a scale, then show piano note names beside a separate C-major-highlighted keyboard, compare C major and D major visually, and show the major-scale chord primer.
- Teach the major-scale chord table, circle of fifths, and circle of fourths in separate tutorial steps. Explain that the circles organize related note roots and help musicians follow common chord movement; show how D–G–C moves down by fifths on one circle and up by fourths on the other.
- After the tutorial, take the visitor to the learning home; do not add a second “skip to progression library” button there because the ordinary library action is already available.
- Explain the major scale and diatonic chord qualities I, ii, iii, IV, V, vi, and vii°.
- If it fits the brief explanation, show vii° as a possible V/vii slash-chord substitution; this is supporting context, not an extra lesson.
- The tutorial is educational content, not a test; learner ratings and saved course progress are not required.

**Acceptance criteria**
- [ ] A first-time visitor can choose an experience level and reach the tutorial or skip it.
- [ ] Skipping the tutorial still allows access to both the databank and song-analysis entry point.
- [ ] The tutorial identifies the seven diatonic major-scale chord qualities and distinguishes major, minor, and diminished symbols clearly.
- [ ] The tutorial supports Next/Back navigation and visually shows keyboard notes, C/D major scale differences, the whole/half-step formula, and the diatonic chord primer.
- [ ] The W–W–H–W–W–W–H formula appears before the first scale example; the piano diagram shows note names on an unhighlighted keyboard and clearly highlights C-major notes in a second diagram.
- [ ] The major chord table, circle-of-fifths lesson, and circle-of-fourths lesson appear separately, with local diagrams and explanations of each circle's purpose.
- [ ] The final tutorial step offers a single finish action and no skip action.
- [ ] The post-tutorial home screen has no redundant “skip to progression library” action, while the standard library entry point remains available.

### Searching and browsing the progression databank

Source: `scope.md > The Unique Kernel`, `The Core Loop`, `The POC Boundary`.

- Search progression entries by their name or Roman-numeral pattern.
- Filter by curated frequency group: frequent, medium, or less common.
- Show a compact grid; each card identifies the progression and its frequency group.
- Keep all diatonic progressions in the frequent or medium groups. Include these four learner-requested non-diatonic examples in the less-common group: I–III–vi, I–III–IV, v–I–IV, and I–II–IV. Explain the altered chord quality and the scale note that changes in each key.
- Frequency is curated learning guidance, not a statistically measured ranking across all online songs.
- Seed examples include:
  - **Frequent:** I–vi–IV–V, vi–IV–I–V, I–IV–V–I, ii–V–I.
  - **Medium:** I–V–vi–IV, I–vi–ii–V, I–ii–IV–V, iii–vi–ii–V, and vi–ii–V–I.
  - **Less common:** I–III–vi, I–III–IV, v–I–IV, I–II–IV.
- Order the grid by group (frequent, medium, less common) and identify each group with a clear text label and green/yellow/red visual treatment.
- Search or filter with no matching entry shows a clear empty state and lets the visitor adjust the query or filter.

**Acceptance criteria**
- [ ] Searching by a progression name or Roman-numeral sequence can find the matching entry.
- [ ] Selecting a frequency group limits the visible cards to that group; clearing the filter restores all entries.
- [ ] Every card shows a progression name, Roman-numeral sequence, and frequency group.
- [ ] Every diatonic entry is frequent or medium, and the four selected non-diatonic entries are in less common.
- [ ] Frequency labels are visually distinct, text-labeled, and clearly described as curated guidance rather than measured statistics.
- [ ] A query with no match displays an explicit “no progressions found” state rather than a blank grid.

### Understanding and hearing a progression

Source: `scope.md > The Unique Kernel`, `The Core Loop`, `What "Working" Looks Like`.

- Opening a card shows the progression name and Roman-numeral sequence, its curated frequency group, a concise explanation of how it is derived or applied, a relevant theory diagram when useful, and an audio example.
- The explanation connects chord movement to the major scale and, where relevant, the circle of fourths/fifths or another useful theory idea.
- For ii–V–I, the explanation may show roots moving by fourths (equivalently, fifths in the opposite direction) and explain how landing on I gives a sense of resolution.
- Show a locally rendered circle-of-fifths diagram in the lesson, highlighting the progression's roots, and explain how it relates to the chord movement.
- Make the synthetic example quieter and give chords more time and space between changes. Use a piano-like, decaying synthetic timbre; it need not be a sampled or recorded piano. Transposition or modulation is not needed.
- Real-song examples are not required for the first version.

**Acceptance criteria**
- [ ] Opening a card reveals its explanation and diagram, if provided, without losing the ability to return to the grid.
- [ ] Each starter entry has a playable, piano-like synthetic audio example that illustrates its progression.
- [ ] Explanations describe a meaningful relationship behind each pattern rather than only restating its chord symbols.
- [ ] Lessons correctly spell diatonic and selected non-diatonic chords in all 12 major keys and show the circle-of-fifths diagram.
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
- Show 4/4 as the low-confidence fallback meter rather than selecting 3/4 from a tie; still label the meter as an estimate and let the visitor correct it.
- Label these estimates clearly and let the visitor correct key, tempo, and time signature before making the chart.
- Offer an **Edit chords** control at the chart preview. In edit mode, show a text field for every beat, including empty beats. Accept supported chord symbols; `N` or `.` means no chord. A correction is placed at that beat's start and can move a chord across a beat or bar boundary by editing both cells. Reject invalid values with a visible, actionable error. The chart must distinguish edited cells from untouched estimates.
- The refreshed chart must calculate section progression matches from the corrected chord labels, and the PDF must use those same corrections. Chord edits invalidate the previous preview until the visitor updates it.
- A separate save action is available only when there are chord corrections and the visitor explicitly confirms they have rights to use the recording as local training data. It saves the source audio and changed intervals under the ignored local feedback folder; it does not upload audio or retrain automatically.
- The visitor supplies the song title and can mark or edit section names and bar ranges such as verse, chorus, and bridge. Cadence does not automatically identify song sections in this POC.
- After the visitor updates the chart preview, compare chord patterns within each confirmed section. Highlight a unique plausible progression match in that section and let the visitor open its databank lesson. Keep unmatched or ambiguous estimates visible without highlighting an unrelated entry or forcing a lesson link.
- An unreadable, unsupported, or failed analysis shows an actionable error, not fabricated results.

**Acceptance criteria**
- [ ] A local audio file can be selected without entering a streaming URL.
- [ ] The result view visibly labels chord, key, tempo, and time-signature output as estimates.
- [ ] The visitor can correct the key, tempo, and time signature and enter a song title before export.
- [ ] The visitor can add or edit section labels; the app does not claim to detect verse/chorus structure automatically.
- [ ] The visitor can edit predicted chord labels from the bar preview; changing labels marks the preview stale, and the updated preview, lesson matches, and PDF consistently reflect those edits.
- [ ] No-feedback, missing-consent, and unsupported-audio cases cannot save training examples. Rights-cleared opt-in examples are stored locally and are not included in the public repository.
- [ ] A unique progression match within a confirmed section is highlighted and links to its corresponding databank lesson; unmatched or ambiguous estimates have no misleading lesson link.
- [ ] An unsupported or unreadable file produces a clear error and no success-shaped result.
- [ ] The app reminds visitors to use audio they are authorized to analyze.
- [ ] A flat/ambiguous meter signal falls back to 4/4 with low confidence rather than returning 3/4 solely because of candidate order; clear synthetic 4/4 accents are detected as 4/4.
- [ ] Saving training feedback requires an explicit rights confirmation and corrected labels, writes audio plus only the manually corrected intervals to the ignored local feedback folder, and never triggers a model update.

### Exporting a performance chart

Source: `scope.md > The Core Loop`, `What "Working" Looks Like`, `The POC Boundary`.

- From the song-analysis result, the visitor can export a printable PDF chart.
- Before export, show a direct bar-lines preview grouped by the visitor's sections, for example `| B . . . | F# . . . | E . D#m . |`. Put the bar number above each measure, show chord names at their estimated beat positions, use dots for empty beats (including no-chord predictions), and do not put beat numbers beside chord names. Start bar 1 at the first predicted chord and exclude any earlier no-chord intro from the chart; if no chord is predicted, retain the full duration and show empty beats. An explicit **Update chart preview** action applies edited section ranges and recalculates bar placement and section-specific progression matches; do not present stale preview data as current.
- Highlight the chord cells that form a unique section progression match. The highlighted chord itself is directly clickable to its lesson; hovering also reveals the progression name, pattern, and key. Do not highlight or link a weak, ambiguous, or unmatched sequence.
- In chord-edit mode, a text input appears for every beat cell, including empty beats. The visitor can enter a supported chord symbol or `N`/`.` for no chord; a changed cell is placed at the start of its beat. Clicking **Done editing** validates and immediately refreshes the chart and progression matches. Invalid and empty values show an actionable error and keep the visitor in edit mode. Untouched predictions remain marked as estimates and user corrections are identified separately.
- Enable PDF download from the latest successfully updated preview. If the visitor changes chart inputs after previewing, ask them to update the preview before downloading.
- The PDF includes the user-supplied song title, key, time signature, song section labels, numbered bars, and estimated chord placements in the same direct bar-lines format. Keep bar numbers separate from chord names, with dots marking empty beats.
- Use corrected key, tempo, and time-signature values in the chart. Include tempo with the chart metadata because it determines bar alignment.
- Keep chord estimates visibly identified as estimates in the PDF, so the chart is not mistaken for verified sheet music.
- Arrange longer songs across as many readable pages as needed; the PDF is for performance reference, not formal notation.

**Acceptance criteria**
- [ ] A visitor can create and open or download a PDF from an analyzed song.
- [ ] The on-screen chart preview groups numbered, pipe-delimited bars under the manually entered section ranges, places chord names on estimated beats, and uses dots for empty beats without adding beat numbers beside chords.
- [ ] Clicking **Update chart preview** after editing metadata or sections recalculates the preview and per-section progression highlights; stale preview data is not presented as current.
- [ ] A unique progression match is highlighted in the relevant section; hovering its chord shows the progression name/pattern/key and a clickable lesson link. Ambiguous/no matches remain unlinked.
- [ ] Clicking a highlighted chord in the preview opens its corresponding lesson directly; the link is not confined to the hover card.
- [ ] Chord edit mode provides one text input for every beat, including empty beats; accepts supported chord symbols plus `N`/`.` for no chord; and rejects invalid input visibly. After updating, the preview, progression matches, and exported PDF use corrected beat placements and distinguish edits from unchanged estimates.
- [ ] Clicking **Done editing** applies valid beat-cell changes to the preview immediately, refreshes progression matches, and enables PDF download from that updated chart; invalid values leave the editor open with an actionable error.
- [ ] Saving corrected training examples requires explicit rights confirmation, stores only corrected intervals and the associated audio locally, and does not change the model until the owner reviews the dataset and runs the opt-in training command.
- [ ] PDF download uses the latest updated preview and is not offered while the preview is stale or invalid.
- [ ] The printout shows title, key, time signature, tempo, song sections, bar numbers, beat markers, and chord labels in a readable layout.
- [ ] The chart reflects user-corrected metadata and manually edited section labels.
- [ ] The PDF clearly notes that chord content is an estimate.
- [ ] If the PDF cannot be generated, explain the failure and leave the on-screen analysis available.

## States and Boundaries

- **First visit:** Experience choice appears; beginners can launch or skip the tutorial.
- **Empty search:** Explain that no progression matched and allow search/filter changes.
- **Uncertain analysis:** Show the experimental-estimate warning in the app and exported chart.
- **Uncertain metadata:** Mark key, tempo, and time signature as estimates and allow correction before export.
- **Weak meter evidence:** Fall back to 4/4 with low confidence instead of treating a candidate-order tie as evidence for 3/4; the visitor can still correct the meter.
- **Chord correction:** Clearly identify user-edited events; refresh progression matches and PDF only from the updated chart.
- **Training feedback:** Store corrected audio locally only after explicit rights confirmation. The owner must review examples and explicitly include eligible songs in a training split; no automatic upload, collection, or retraining.
- **No or ambiguous section match:** Keep chord estimates visible but do not highlight or link an unrelated databank entry.
- **No-chord opening:** Start bar 1 at the first predicted chord and omit the preceding no-chord intro; if no chord is predicted anywhere, retain the recording duration and show dots.
- **Stale chart preview:** Mark the preview as out of date after chart inputs change and require **Update chart preview** before PDF download.
- **Missing title or section labels:** Prompt the visitor to provide a title; section labels may be left blank or edited before export.
- **Analysis or PDF error:** Explain the failure and do not display fabricated results; retain any valid on-screen analysis if only export failed.
- **Rights and privacy:** Analyze only local audio the visitor is authorized to use. The app never uploads audio; by default, visitor audio is temporary and removed after analysis. A separate explicit rights confirmation is required to save corrected audio intervals under ignored local storage for owner review. Those feedback files are never included in the public repository. The learner confirmed their original training recordings and performances may be included in the public demo/repository.
- **Frequency boundary:** Frequency groups are curated guidance, not measured claims about all songs.
- **Persistence:** No account, ratings, or saved learning history in this POC. Visitor uploads and results are temporary unless the visitor explicitly confirms rights and saves corrected audio intervals to the local training-feedback folder.

## Product Decisions

- Keep **Cadence** and the tagline **“Resolve Every Song.”**
- Keep the educational progression databank as the main differentiator and add a small chord-label training experiment using the learner's original, chord-labeled recordings.
- Train the model before visitor use; show the training and held-out evaluation in the demo, then let visitors use the pre-trained model without training.
- Compare the trained model with the existing chord-template analyzer on the same held-out song to check whether training helped; report the result honestly.
- Derive progression candidates from chord predictions rather than training a second progression model.
- Let visitors analyze authorized local audio, including full-band recordings, while clearly labeling model outputs as experimental.
- Estimate key, tempo, and time signature in the app and allow visitors to correct those values. Visitors supply the song title and mark or edit song sections.
- Include an in-preview chord editor, a section-aware bar/beat preview with an explicit update action, and a printable PDF generated from the confirmed preview; do not build automatic song-section detection.
- Save corrected training intervals only after explicit rights confirmation, locally and outside the public repository. The owner reviews and assigns feedback songs to the training split, then chooses a separate opt-in training command; do not automatically retrain or include feedback in default training runs.
- Use the learner's ranked starter groups: frequent (I–vi–IV–V, vi–IV–I–V, I–IV–V–I, ii–V–I), medium (the remaining diatonic examples), and less common (I–III–vi, I–III–IV, v–I–IV, I–II–IV).
- Explain frequency groups as curated learning guidance, not a survey.
- Start the beginner path with the major scale and diatonic chord qualities, then identify the altered note in each selected non-diatonic example.
- Use a warm, minimal jazz-club visual mood with restrained decorative details.

## What We're Building

- Welcome experience choice and a short optional major-scale primer.
- A small searchable/filterable databank of diatonic major-key progressions and four selected non-diatonic patterns, with lessons and synthetic audio.
- A reproducible training run and held-out evaluation for a chord-label model trained from the learner's labeled original recordings.
- Local analysis of visitor-provided audio using the pre-trained model, with estimated and editable key/tempo/time-signature details.
- A refreshable, section-aware bar/beat chord chart with user-provided title, corrected metadata, and section labels; highlight plausible progression matches with lesson links and export the confirmed preview as a printable PDF.
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

- Resolved: the learner selected I–III–vi, I–III–IV, v–I–IV, and I–II–IV for the less-common group because they appear in Demo 4.
- Which chord-label vocabulary and local audio formats can the model support reliably? Settle the bounded label set and WAV/MP3 behavior in `4-spec` before implementation.
- What training-label file format is simplest for the learner to prepare from their annotated recordings? Decide in `4-spec`; automatic PDF reading is deferred.
