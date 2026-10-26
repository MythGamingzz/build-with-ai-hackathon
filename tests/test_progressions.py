import json
import tempfile
import unittest
from pathlib import Path

from cadence.progression_data import (
    FREQUENCY_GROUPS,
    load_progressions,
    search_progressions,
)


class ProgressionCatalogTests(unittest.TestCase):
    def test_catalog_contains_seed_and_selected_chromatic_patterns(self) -> None:
        progressions = load_progressions()
        patterns = {progression.pattern for progression in progressions}

        self.assertTrue(
            {
                "I-vi-IV-V",
                "vi-IV-I-V",
                "I-IV-V-I",
                "ii-V-I",
                "I-V-vi-IV",
                "I-vi-ii-V",
                "I-III-vi",
                "I-III-IV",
                "v-I-IV",
                "I-II-IV",
            }.issubset(patterns)
        )
        self.assertEqual({entry.frequency for entry in progressions}, set(FREQUENCY_GROUPS))
        self.assertTrue(
            all(
                len(entry.degrees) == len(entry.roman_numerals) == len(entry.qualities)
                for entry in progressions
            )
        )
        expected_diatonic = ("major", "minor", "minor", "major", "major", "minor", "diminished")
        for entry in progressions:
            is_diatonic = all(
                quality == expected_diatonic[degree - 1]
                for degree, quality in zip(entry.degrees, entry.qualities, strict=True)
            )
            self.assertEqual(entry.frequency == "less common", not is_diatonic)

    def test_results_are_ordered_by_curated_frequency_group(self) -> None:
        progressions = load_progressions()

        results = search_progressions(progressions)
        ranks = [FREQUENCY_GROUPS.index(entry.frequency) for entry in results]

        self.assertEqual(ranks, sorted(ranks))

    def test_searches_by_name_or_roman_numerals_and_filters_frequency(self) -> None:
        progressions = load_progressions()

        by_name = search_progressions(progressions, query="ii–V–I")
        by_pattern = search_progressions(progressions, query="I vi ii V", frequency="medium")
        frequent = search_progressions(progressions, frequency="frequent")

        self.assertEqual([entry.id for entry in by_name], ["ii-V-I"])
        self.assertEqual([entry.id for entry in by_pattern], ["I-vi-ii-V"])
        self.assertTrue(all(entry.frequency == "frequent" for entry in frequent))

    def test_empty_search_has_no_results_and_invalid_filter_is_rejected(self) -> None:
        progressions = load_progressions()

        self.assertEqual(search_progressions(progressions, query="not-a-progression"), ())
        with self.assertRaisesRegex(ValueError, "Unsupported frequency group"):
            search_progressions(progressions, frequency="objective")

    def test_rejects_catalog_degree_and_roman_numeral_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "progressions.json"
            path.write_text(
                json.dumps(
                    [
                        {
                            "id": "bad",
                            "name": "Bad progression",
                            "roman_numerals": ["I", "V"],
                            "degrees": [1, 4],
                            "qualities": ["major", "major"],
                            "frequency": "frequent",
                            "description": "Invalid data.",
                            "theory_relationship": "Invalid degree mapping.",
                        }
                    ]
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "do not match"):
                load_progressions(path)


if __name__ == "__main__":
    unittest.main()
