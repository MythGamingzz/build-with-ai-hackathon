import unittest
from dataclasses import replace

from cadence.matching import match_progression
from cadence.progression_data import load_progressions
from cadence.theory import spell_progression


class ProgressionMatchingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.progressions = load_progressions()
        cls.target = next(
            progression
            for progression in cls.progressions
            if progression.roman_numerals == ("I", "vi", "IV", "V")
        )

    def test_matches_a_catalog_pattern_in_another_major_key(self) -> None:
        chords = spell_progression(
            self.target.degrees,
            "D",
            self.target.qualities,
        )
        labels = [chord.symbol for chord in chords]

        match = match_progression(
            ["N", labels[0], labels[0], *labels[1:]],
            self.progressions,
        )

        self.assertIs(match.progression, self.target)
        self.assertEqual(match.key, "D")
        self.assertFalse(match.ambiguous)

    def test_does_not_link_when_multiple_patterns_fit(self) -> None:
        duplicate = replace(
            self.target,
            id="duplicate-pattern",
            name="Duplicate pattern",
        )
        chords = spell_progression(
            self.target.degrees,
            "C",
            self.target.qualities,
        )

        match = match_progression(
            [chord.symbol for chord in chords],
            self.progressions + (duplicate,),
        )

        self.assertIsNone(match.progression)
        self.assertTrue(match.ambiguous)
        self.assertIn(self.target.name, match.candidate_names)
        self.assertIn("Duplicate pattern", match.candidate_names)

    def test_returns_no_match_for_an_unrelated_short_sequence(self) -> None:
        match = match_progression(["C"], self.progressions)

        self.assertIsNone(match.progression)
        self.assertFalse(match.ambiguous)
        self.assertEqual(match.candidate_names, ())


if __name__ == "__main__":
    unittest.main()
