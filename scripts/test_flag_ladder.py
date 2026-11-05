"""Tests for the ladder in scripts/flag_ladder.py. Made-up sources only, no files."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import c02_cfc11 as c  # noqa: E402
import flag_ladder as fl  # noqa: E402

M0 = c.idx(2010, 1)
ALL = range(M0 - 20, M0 + 60)  # every source is tested all through, unless a test says otherwise


def src(lab, code, flags=(), tested=ALL):
    return fl.make_source(lab, code, flags, tested)


def at(sources, month):
    return fl.ladder(sources, month, month)[0]


def many(prefix_lab, codes, flag_month):
    return [src(prefix_lab, code, [flag_month]) for code in codes]


NORTH_N = ["alt", "brw", "mhd", "nwr", "kum", "sum"]
NORTH_A = ["mhd", "thd", "rpb", "jfj", "cmn", "zzz"]


class Ladder(unittest.TestCase):
    def test_no_flags_is_level_0(self):
        m = at([src("NOAA", "alt"), src("AGAGE", "mhd")], M0)
        self.assertEqual((m["level"], m["count"]), (0, 0))

    def test_one_source_is_level_1(self):
        self.assertEqual(at([src("NOAA", "alt", [M0])], M0)["level"], 1)

    def test_two_sources_same_lab_is_level_2(self):
        self.assertEqual(at(many("NOAA", ["alt", "brw"], M0), M0)["level"], 2)

    def test_two_sources_two_labs_is_level_2(self):
        s = [src("NOAA", "alt", [M0]), src("AGAGE", "mhd", [M0])]
        self.assertEqual(at(s, M0)["level"], 2)

    def test_three_sources_one_lab_is_level_2_and_one_lab_3plus(self):
        m = at(many("NOAA", ["alt", "brw", "mhd"], M0), M0)
        self.assertEqual(m["level"], 2)
        self.assertTrue(m["one_lab_3plus"])

    def test_three_sources_two_labs_is_level_3(self):
        s = many("NOAA", ["alt", "brw"], M0) + many("AGAGE", ["mhd"], M0)
        m = at(s, M0)
        self.assertEqual(m["level"], 3)
        self.assertFalse(m["one_lab_3plus"])

    def test_ten_sources_two_labs_north_only_is_level_3(self):
        s = many("NOAA", NORTH_N, M0) + many("AGAGE", NORTH_A[:4], M0)
        self.assertEqual(len(s), 10)
        self.assertEqual(at(s, M0)["level"], 3)

    def test_ten_sources_one_lab_both_hemispheres_is_level_2(self):
        s = many("NOAA", NORTH_N + ["spo", "psa", "cgo", "smo"], M0)
        self.assertEqual(len(s), 10)
        self.assertEqual(at(s, M0)["level"], 2)

    def test_ten_sources_two_labs_both_hemispheres_is_level_4(self):
        s = many("NOAA", NORTH_N[:4] + ["spo", "cgo"], M0) + many("AGAGE", ["mhd", "thd", "rpb", "smo"], M0)
        self.assertEqual(len(s), 10)
        self.assertEqual(at(s, M0)["level"], 4)

    def test_flag_11_months_back_counts_and_12_does_not(self):
        s = [src("NOAA", "alt", [M0])]
        self.assertEqual(at(s, M0 + 11)["count"], 1)
        self.assertEqual(at(s, M0 + 12)["count"], 0)

    def test_one_source_flagging_five_times_counts_once(self):
        s = [src("NOAA", "alt", [M0, M0 + 1, M0 + 2, M0 + 3, M0 + 4])]
        self.assertEqual(at(s, M0 + 4)["count"], 1)

    def test_three_sources_from_two_labs_make_level_3_possible(self):
        s = [src("NOAA", "alt"), src("NOAA", "brw"), src("AGAGE", "mhd")]
        self.assertTrue(at(s, M0)["possible"])

    def test_three_sources_from_one_lab_do_not(self):
        s = [src("NOAA", "alt"), src("NOAA", "brw"), src("NOAA", "mhd")]
        self.assertFalse(at(s, M0)["possible"])

    def test_two_sources_from_two_labs_do_not(self):
        s = [src("NOAA", "alt"), src("AGAGE", "mhd")]
        self.assertFalse(at(s, M0)["possible"])

    def test_tested_11_months_back_counts_then_12_does_not(self):
        s = [src("NOAA", "alt", tested=[M0]), src("NOAA", "brw", tested=[M0]), src("AGAGE", "mhd", tested=[M0])]
        self.assertTrue(at(s, M0 + 11)["possible"])
        self.assertFalse(at(s, M0 + 12)["possible"])

    def test_level_3_for_5_months_then_a_gap_then_2_more_is_2_runs(self):
        levels = [3] * 5 + [2] + [3] * 2
        self.assertEqual(fl.runs(levels), 2)
        self.assertEqual(fl.runs([4, 3, 3, 4]), 1)  # level 4 inside a run does not split it
        self.assertEqual(fl.runs([0, 1, 2]), 0)

    def test_level_18_uses_only_the_18_sources(self):
        s = many("NOAA", ["alt"], M0) + many("AGAGE", ["jfj", "cmn"], M0)
        m = at(s, M0)
        self.assertEqual((m["level"], m["level_18"], m["count_18"]), (3, 1, 1))

    def test_flag_outside_tested_months_is_refused(self):
        with self.assertRaises(ValueError):
            fl.make_source("NOAA", "alt", [M0], [M0 + 1])

    def test_south_and_set_membership(self):
        self.assertTrue(src("AGAGE", "cgo").south)
        self.assertFalse(src("AGAGE", "rpb").south)
        self.assertTrue(src("NOAA", "psa").south)
        self.assertTrue(src("AGAGE", "gsn").in_cfc11_set)
        self.assertFalse(src("AGAGE", "jfj").in_cfc11_set)
        self.assertEqual(len(fl.CFC11_SET), 18)


if __name__ == "__main__":
    unittest.main()
