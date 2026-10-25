---
doc: scope
status: approved
---

# Cadence

Resolve Every Song.

A local music-analysis experiment that estimates chords and transcribes sung lyrics from a short learner-provided piano-and-vocal recording.

## The Unique Kernel
Help a musician review their own recording by placing estimated chord changes alongside the words they sang, so they can compare the analysis with what they intended to play.

## Who It's For
Musicians experimenting with how software can identify chords and words in a recording they made themselves.

## The Core Loop
The musician provides a short local piano-and-vocal recording. A local Python analysis tool estimates sung words and chord changes with timestamps, then presents the two on a shared timeline. The musician compares those estimates with a hand-checked reference for the recording and notes where the analysis succeeded or failed.

## Inspiration & Identity
Keep the analysis transparent: distinguish software estimates from the musician's verified reference and make timing and mismatches easy to inspect.

## Why This Matters to the Learner
The team wants to explore whether software can make chord transcription more efficient. Timothy will provide a piano-and-vocal recording for the first experiment.

## What "Working" Looks Like
In a private local demonstration, the musician runs the tool on one piano-and-vocal recording. It produces time-stamped word and chord estimates, displays them together, and compares them with a hand-checked reference. The demonstration shows the analysis process and its observed errors; one recording does not establish reliable results on other songs.

## The POC Boundary
- A local Python analysis experiment, not a deployed website.
- One short, locally stored PCM WAV recording with piano accompaniment and Timothy's own sung vocal.
- Automatic sung-word transcription and word/segment timing using an existing locally runnable speech-recognition tool, if its license and singing performance are suitable.
- Estimated chord labels and time ranges using a separately evaluated chord-analysis tool, which may use signal processing rather than a trained AI model.
- A readable report that places estimated lyrics and chords together and compares them with a manually checked reference.
- Keep the recording local; do not send it to a hosted service.
- Keep the recording, transcript, reference, and generated report private; do not publish this recording or its analysis as a demo.
- Report observed results honestly; this experiment does not promise high accuracy or generalization.

## Later
- Test additional original or appropriately licensed recordings and instruments.
- Explore training or fine-tuning a model using a larger, properly licensed, hand-labeled dataset.
- Consider a web interface or a broader musician-facing application after local analysis feasibility is demonstrated.

## Explicitly Cut
- YouTube/Spotify link ingestion, downloading from platforms, and analysis of songs without authorization are outside this experiment.
- Guitar, bass, drums, multiple simultaneous instrument tracks, and arbitrary user songs are not part of the first recording test.
- Training a new model from scratch, claims of high accuracy, a hosted service, a web application, song repository, history, settings, playback controls, transposition, and music-theory lessons are not part of this first prototype.
