import unittest

from cadence.theory import (
    MAJOR_KEYS,
    diatonic_chords,
    major_scale,
    note_pitch_class,
    spell_progression,
)


class ScaleTheoryTests(unittest.TestCase):
    def test_c_major_diatonic_chords_have_expected_qualities_and_spellings(self) -> None:
        chords = diatonic_chords("C")

        self.assertEqual(
            [chord.symbol for chord in chords],
            ["C", "Dm", "Em", "F", "G", "Am", "B°"],
        )
        self.assertEqual(chords[-1].notes, ("B", "D", "F"))

    def test_spell_progression_in_multiple_major_keys(self) -> None:
        c_major = spell_progression([1, 6, 4, 5], "C")
        db_major = spell_progression([1, 6, 4, 5], "Db")

        self.assertEqual([chord.symbol for chord in c_major], ["C", "Am", "F", "G"])
        self.assertEqual(
            [chord.symbol for chord in db_major],
            ["Db", "Bbm", "Gb", "Ab"],
        )

    def test_all_twelve_major_keys_have_seven_diatonic_chords(self) -> None:
        self.assertEqual(len(set(MAJOR_KEYS)), 12)
        self.assertTrue(all(len(diatonic_chords(key)) == 7 for key in MAJOR_KEYS))

    def test_selected_chromatic_progressions_have_correct_c_major_chords(self) -> None:
        major_three = spell_progression([1, 3, 6], "C", ["major", "major", "minor"])
        major_two = spell_progression([1, 2, 4], "C", ["major", "major", "major"])
        minor_five = spell_progression([5, 1, 4], "C", ["minor", "major", "major"])

        self.assertEqual([chord.roman_numeral for chord in major_three], ["I", "III", "vi"])
        self.assertEqual(major_three[1].notes, ("E", "G#", "B"))
        self.assertEqual([chord.symbol for chord in major_two], ["C", "D", "F"])
        self.assertEqual(major_two[1].notes, ("D", "F#", "A"))
        self.assertEqual([chord.symbol for chord in minor_five], ["Gm", "C", "F"])
        self.assertEqual(minor_five[0].notes, ("G", "Bb", "D"))

    def test_chromatic_chord_qualities_spell_correctly_in_all_major_keys(self) -> None:
        degrees = [1, 3, 6, 5, 1, 2, 4]
        qualities = ["major", "major", "minor", "minor", "major", "major", "major"]
        expected_intervals = {
            "major": (0, 4, 7),
            "minor": (0, 3, 7),
        }

        for key in MAJOR_KEYS:
            with self.subTest(key=key):
                chords = spell_progression(degrees, key, qualities)
                for chord, quality in zip(chords, qualities, strict=True):
                    root_pitch = note_pitch_class(chord.notes[0])
                    intervals = tuple(
                        (note_pitch_class(note) - root_pitch) % 12
                        for note in chord.notes
                    )
                    self.assertEqual(intervals, expected_intervals[quality])

    def test_rejects_unknown_keys_and_invalid_degrees(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported major key"):
            major_scale("H")
        with self.assertRaisesRegex(ValueError, "integers from 1 through 7"):
            spell_progression([1, 8], "C")
        with self.assertRaisesRegex(ValueError, "one quality per degree"):
            spell_progression([1, 3], "C", ["major"])
        with self.assertRaisesRegex(ValueError, "Unsupported triad quality"):
            spell_progression([1], "C", ["augmented"])


if __name__ == "__main__":
    unittest.main()
