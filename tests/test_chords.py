import unittest

import numpy as np

from cadence.chords import (
    CHORD_LABELS,
    NO_CHORD_INDEX,
    chord_events,
    classify_chroma,
    mask_low_energy_frames,
    merge_short_runs,
    smooth_labels,
)


class ChordAnalysisTests(unittest.TestCase):
    def test_classifies_major_and_minor_chroma_templates(self) -> None:
        chroma = np.zeros((12, 2), dtype=np.float32)
        chroma[[0, 4, 7], 0] = 1
        chroma[[2, 5, 9], 1] = 1

        labels, scores = classify_chroma(chroma)

        self.assertEqual([CHORD_LABELS[index] for index in labels], ["C", "Dm"])
        self.assertTrue(np.all(scores[labels, np.arange(2)] > 0.9))

    def test_silent_chroma_is_not_mislabeled_as_a_chord(self) -> None:
        labels, _ = classify_chroma(np.zeros((12, 1), dtype=np.float32))

        self.assertEqual(labels.tolist(), [NO_CHORD_INDEX])

    def test_merges_short_runs_into_the_longer_neighbor(self) -> None:
        labels = np.array([0, 0, 1, 1, 1, 2, 2, 2, 2, 3, 3], dtype=np.int64)

        merged = merge_short_runs(labels, minimum_frames=3)

        np.testing.assert_array_equal(
            merged,
            np.array([1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2], dtype=np.int64),
        )

    def test_masks_frames_below_relative_audio_energy_floor(self) -> None:
        labels = np.array([0, 1, 2], dtype=np.int64)
        rms = np.array([0.0, 0.00005, 0.1], dtype=np.float32)

        masked = mask_low_energy_frames(labels, rms)

        np.testing.assert_array_equal(
            masked,
            np.array([NO_CHORD_INDEX, NO_CHORD_INDEX, 2], dtype=np.int64),
        )

    def test_smoothing_reduces_one_frame_switch(self) -> None:
        labels = np.array([0, 0, 1, 0, 0], dtype=np.int64)

        smoothed = smooth_labels(labels)

        np.testing.assert_array_equal(smoothed, [0, 0, 0, 0, 0])

    def test_events_merge_adjacent_frames_and_clip_to_audio_length(self) -> None:
        labels = np.array([0, 0, 2], dtype=np.int64)
        scores = np.zeros((len(CHORD_LABELS), 3), dtype=np.float32)
        scores[0, :2] = [0.9, 0.8]
        scores[2, 2] = 0.7

        events = chord_events(labels, scores, frame_seconds=0.5, duration=1.2)

        self.assertEqual([event["label"] for event in events], ["C", "C#"])
        self.assertEqual(events[0]["start"], 0)
        self.assertEqual(events[0]["end"], 1.0)
        self.assertEqual(events[1]["end"], 1.2)


if __name__ == "__main__":
    unittest.main()
