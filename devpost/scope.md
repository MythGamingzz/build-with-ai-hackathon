---
doc: scope
status: approved
---

# Cadence

Resolve Every Song.

An educational chord-progression databank paired with a small local experiment that learns chord labels from annotated original recordings and estimates chords in new local songs.

## The Unique Kernel
Cadence helps musicians understand why familiar progressions work, then connects that learning library to a transparent experiment: train a model to predict chord labels from the team's own annotated recordings, use it to estimate chords in new local songs, and derive likely progression patterns from those predictions. The project demonstrates what the model learns on held-out music without claiming reliable transcription of arbitrary songs.

## Who It's For
Musicians who want to understand the patterns behind chord progressions, especially beginners who have played from chord sheets without knowing why the chords work, and curious musicians who want to see how a small chord-learning model is trained and evaluated.

## The Core Loop
The musician chooses their experience level and can take a short major-scale tutorial. They search the progression databank, listen to an example, and learn the theory behind a pattern. In the training experiment, the team provides original recordings with chord changes annotated by bar or approximate time and trains a chord-label predictor. A visitor can then provide an authorized local song to see experimental chord estimates and derived progression candidates, correct estimated musical details, mark song sections, and export a printable bar-and-beat chord chart.

## Inspiration & Identity
Make music theory feel like discovering patterns rather than memorizing rules. Keep explanations approachable, examples easy to compare by ear, and frequency labels clearly identified as curated learning guidance rather than measured internet-wide statistics. Keep the model experiment local, understandable, and honest about its limits.

## Why This Matters to the Learner
Timothy described playing from chord notes without thinking much about why the chords were used. Discovering that scales, the circle of fourths/fifths, and other relationships create patterns made it exciting to explore progressions instead of guessing. He also wants to explore training a chord model on his own original songs.

## What "Working" Looks Like
In a short public demo, a newcomer learns a major-scale chord quality, finds and hears a familiar progression, and understands why its chord movement works. The demo then shows the model trained on annotated original recordings, estimates chords in a new local song, and turns those labels into an uncertain progression candidate that can open a related lesson. The visitor can correct estimated key, tempo, and time signature, add a title and section labels, and print a chord chart. The team also evaluates predictions against reference labels on a song kept out of training. The measured result may be imperfect; the demo succeeds by showing the training and an honest evaluation, not by promising high accuracy.

## The POC Boundary
- Keep the searchable, listenable progression databank and beginner-friendly lessons as the product's educational core.
- Include a paced, skippable major-scale tutorial that introduces the whole/half-step pattern before scale examples, then teaches piano note names, compares C and D major, and presents the chord primer and circles of fifths and fourths separately, explaining how each circle helps musicians understand related keys and chord movement.
- Include a small curated set of diatonic major-key progressions and four learner-requested non-diatonic patterns (I–III–vi, I–III–IV, v–I–IV, and I–II–IV), with explanations, theory diagrams, all-key spellings, and original piano-like synthetic audio. Keep diatonic patterns in frequent/medium and the four chromatic patterns in less common; these are curated learning groups, not measured prevalence.
- Add a small, local supervised experiment that learns individual chord labels from the learner's original recordings annotated with chord changes and approximate bar or time boundaries.
- Let a visitor provide an authorized local audio file for experimental chord predictions from the trained model; keep audio processing local and make uncertainty visible.
- Derive progression candidates from predicted chord labels using a clear deterministic step; do not train a separate progression model.
- Let visitors correct estimated key, tempo, and time signature, enter a song title, mark or edit section names, and export a printable chart with chord placements by bar and beat.
- Evaluate on at least one original song held out from training when the available recordings allow it. Show the reference labels beside predictions and report limitations; if the dataset is too small for a meaningful song-level holdout, say so rather than implying generalization.
- Full-band recordings are allowed; instrument separation is not required. Their more complex mix may make chord prediction harder.
- The learner confirmed that the original recordings and performances are theirs and may be shared publicly. Keep the public demo and repository limited to those authorized original assets and their annotations.
- Keep all model predictions experimental; do not claim accurate recognition of arbitrary songs.
- Do not automatically identify verse/chorus/bridge sections; visitors mark or edit those labels for the printout.

## Later
- More annotated songs, musical styles, keys, chord qualities, and a larger training/evaluation set.
- Better model performance after measuring errors and gathering additional rights-cleared labeled material.
- Broader local-song analysis, instrument separation, a deployed product, accounts, and saved personal collections.
- A sourced frequency survey based on a defined, representative, properly licensed song collection.

## Explicitly Cut
- A general-purpose analyzer that promises accurate recognition on arbitrary songs; user-provided song results remain experimental, and the training experiment is a small, measured proof of concept.
- A separately trained progression classifier; progression candidates are derived from chord predictions so the experiment stays small and inspectable.
- Streaming links, platform downloads, hosted inference, or uploading audio to a remote service.
- A broad catalog of chromatic progressions beyond the four selected examples; the beginner path still starts with ordinary diatonic major-scale chord qualities.
- An exhaustive, objectively ranked internet-wide progression catalog; curated frequency groups are learning guidance, not survey results.
