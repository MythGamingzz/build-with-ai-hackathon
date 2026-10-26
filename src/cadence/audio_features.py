from dataclasses import dataclass
from pathlib import Path

import librosa
import numpy as np
from numpy.typing import NDArray
from scipy.ndimage import uniform_filter1d

SAMPLE_RATE = 22050
HOP_LENGTH = 512
CHROMA_AVERAGE_FRAMES = 21


@dataclass(frozen=True)
class AudioFeatures:
    chroma: NDArray[np.float32]
    rms: NDArray[np.float32]
    sample_rate: int
    duration: float


def load_audio_features(audio_path: Path) -> AudioFeatures:
    audio, sample_rate = librosa.load(audio_path, sr=SAMPLE_RATE, mono=True)
    if audio.size == 0:
        raise ValueError(f"The audio file contains no samples: {audio_path}")

    chroma = librosa.feature.chroma_cqt(
        y=audio,
        sr=sample_rate,
        hop_length=HOP_LENGTH,
    )
    chroma = uniform_filter1d(
        chroma,
        size=CHROMA_AVERAGE_FRAMES,
        axis=1,
        mode="nearest",
    ).astype(np.float32)
    rms = librosa.feature.rms(
        y=audio,
        frame_length=2048,
        hop_length=HOP_LENGTH,
    )[0].astype(np.float32)
    if chroma.shape[1] != rms.size:
        raise ValueError(
            f"Audio feature lengths do not match for {audio_path}: "
            f"{chroma.shape[1]} chroma frames and {rms.size} RMS frames."
        )

    return AudioFeatures(
        chroma=chroma,
        rms=rms,
        sample_rate=sample_rate,
        duration=len(audio) / sample_rate,
    )
