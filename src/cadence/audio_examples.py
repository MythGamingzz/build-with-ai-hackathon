import io
import math
import wave
from collections.abc import Sequence

import numpy as np

from cadence.theory import note_pitch_class, spell_progression

SAMPLE_RATE = 22050
CHORD_SECONDS = 1.25
GAP_SECONDS = 0.55
PEAK_AMPLITUDE = 0.22
_PIANO_HARMONICS = ((1, 1.0), (2, 0.42), (3, 0.2), (4, 0.1), (5, 0.045))
_PIANO_LEVEL = sum(amplitude for _, amplitude in _PIANO_HARMONICS)


def _piano_note(midi_note: int, time: np.ndarray) -> np.ndarray:
    fundamental = 440 * 2 ** ((midi_note - 69) / 12)
    signal = np.zeros_like(time)
    for harmonic, amplitude in _PIANO_HARMONICS:
        partial = np.sin(2 * np.pi * fundamental * harmonic * time)
        partial_decay = np.exp(-time * (1.8 + 0.22 * (harmonic - 1)))
        signal += amplitude * partial * partial_decay
    attack = 1 - np.exp(-time * 85)
    return signal * attack


def generate_progression_wav(
    degrees: Sequence[int],
    key: str = "C",
    chord_seconds: float = CHORD_SECONDS,
    sample_rate: int = SAMPLE_RATE,
    qualities: Sequence[str] | None = None,
    gap_seconds: float = GAP_SECONDS,
) -> bytes:
    if not math.isfinite(chord_seconds) or chord_seconds <= 0:
        raise ValueError("Chord duration must be finite and positive.")
    if not math.isfinite(gap_seconds) or gap_seconds < 0:
        raise ValueError("Gap duration must be finite and non-negative.")
    if (
        not isinstance(sample_rate, int)
        or isinstance(sample_rate, bool)
        or sample_rate < 8000
    ):
        raise ValueError("Sample rate must be an integer at least 8000 Hz.")
    chords = spell_progression(degrees, key, qualities)
    sample_count = max(1, round(chord_seconds * sample_rate))
    gap_sample_count = round(gap_seconds * sample_rate)
    time = np.arange(sample_count, dtype=np.float32) / sample_rate
    release = min(sample_count, max(1, round(0.045 * sample_rate)))
    release_envelope = np.ones(sample_count, dtype=np.float32)
    release_envelope[-release:] = np.linspace(1, 0, release, dtype=np.float32)

    segments = []
    for chord in chords:
        signal = np.zeros(sample_count, dtype=np.float32)
        midi_notes = []
        for note in chord.notes:
            midi_note = 60 + note_pitch_class(note)
            while midi_notes and midi_note <= midi_notes[-1]:
                midi_note += 12
            midi_notes.append(midi_note)
        for midi_note in midi_notes:
            signal += _piano_note(midi_note, time)
        segments.append(signal * release_envelope / (len(chord.notes) * _PIANO_LEVEL))

    silence = np.zeros(gap_sample_count, dtype=np.float32)
    audio_parts = []
    for index, segment in enumerate(segments):
        if index:
            audio_parts.append(silence)
        audio_parts.append(segment)
    audio = np.concatenate(audio_parts)
    peak = float(np.max(np.abs(audio)))
    if peak > 0:
        audio = audio * (PEAK_AMPLITUDE / peak)
    pcm = np.round(audio * 32767).astype("<i2")

    output = io.BytesIO()
    with wave.open(output, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm.tobytes())
    return output.getvalue()
