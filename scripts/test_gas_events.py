"""Tests for scripts/gas_events.py. Made-up data only, written to temp folders."""
import contextlib
import csv
import io
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import c02_cfc11 as c  # noqa: E402
import clean_gases as g  # noqa: E402
import flag_ladder as fl  # noqa: E402
import gas_events as ge  # noqa: E402
from test_clean_gases import (AGAGE_CODES, FROM, MC, NOAA_CODES, Base, monthly_rows,  # noqa: E402
                              straight, write_nc, write_table)

EVENT = {"gas": "made-up", "group": "made-up", "began": "2010-01", "public": "2011-01-15"}


def sources(noaa=3, agage=3, first=c.idx(2008, 1), last=c.idx(2012, 12)):
    out = []
    for lab, n in (("NOAA", noaa), ("AGAGE", agage)):
        for k in range(n):
            out.append(fl.make_source(lab, f"s{k}", [], range(first, last + 1)))
    return out


def months(levels, first=c.idx(2009, 1), last=c.idx(2011, 12)):
    """levels: {month index: level}. One ladder-shaped dict per month, possible everywhere."""
    return [{"month": i, "level": levels.get(i, 0), "count": 3 if levels.get(i, 0) >= 3 else 0, "possible": True}
            for i in range(first, last + 1)]


def scored(levels, event=EVENT, **kw):
    return ge.score(months(levels, **kw), sources(), event)


class Scoring(unittest.TestCase):
    def test_level_3_inside_the_stretch_is_a_hit_in_the_right_month(self):
        r = scored({c.idx(2010, 6): 3})
        self.assertEqual((r["outcome"], r["first_level_3"], r["sources_at_first_level_3"]), ("hit", "2010-06", 3))
        self.assertEqual(r["lead_months"], 7)

    def test_level_4_with_no_month_at_exactly_3_is_a_hit(self):
        r = scored({c.idx(2010, 6): 4, c.idx(2010, 7): 4})
        self.assertEqual((r["outcome"], r["first_level_3"]), ("hit", "2010-06"))

    def test_level_3_in_the_last_month_before_the_public_month_is_a_hit_with_lead_1(self):
        r = scored({c.idx(2010, 12): 3})
        self.assertEqual((r["outcome"], r["lead_months"]), ("hit", 1))

    def test_level_3_only_in_the_public_month_is_a_miss(self):
        self.assertEqual(scored({c.idx(2011, 1): 3})["outcome"], "miss")

    def test_level_3_only_after_the_public_month_is_a_miss(self):
        self.assertEqual(scored({c.idx(2011, 6): 3, c.idx(2011, 7): 4})["outcome"], "miss")

    def test_level_2_at_most_is_a_miss(self):
        r = scored({c.idx(2010, 6): 2, c.idx(2010, 7): 2})
        self.assertEqual((r["outcome"], r["first_level_3"], r["lead_months"]), ("miss", None, None))

    def test_level_3_in_the_month_the_change_began_is_a_hit_not_a_false_alarm(self):
        r = scored({c.idx(2010, 1): 3})
        self.assertEqual((r["outcome"], r["false_alarm"], r["first_false_level_3"]), ("hit", False, None))

    def test_level_3_the_month_before_it_began_is_a_false_alarm(self):
        r = scored({c.idx(2009, 12): 3})
        self.assertEqual((r["outcome"], r["false_alarm"], r["first_false_level_3"]), ("miss", True, "2009-12"))

    def test_a_hit_and_a_false_alarm_on_one_gas_are_both_reported(self):
        r = scored({c.idx(2009, 5): 4, c.idx(2010, 3): 3})
        self.assertEqual((r["outcome"], r["false_alarm"], r["first_false_level_3"], r["first_level_3"]),
                         ("hit", True, "2009-05", "2010-03"))

    def test_2_sources_tested_in_the_stretch_is_not_testable(self):
        r = ge.score(months({c.idx(2010, 6): 3}), sources(1, 1), EVENT)
        self.assertEqual((r["outcome"], r["first_level_3"], r["lead_months"]), ("not testable", None, None))

    def test_5_sources_tested_all_one_lab_is_not_testable(self):
        r = ge.score(months({c.idx(2010, 6): 3}), sources(5, 0), EVENT)
        self.assertEqual((r["outcome"], r["tested_noaa"], r["tested_agage"]), ("not testable", 5, 0))

    def test_sources_tested_only_outside_the_stretch_do_not_count(self):
        src = sources(2, 2) + [fl.make_source("NOAA", "late", [], [c.idx(2012, 1)]),
                               fl.make_source("AGAGE", "early", [], [c.idx(2009, 1)])]
        self.assertEqual(ge.score(months({}), src, EVENT)["outcome"], "miss")
        src = sources(1, 1) + [fl.make_source("NOAA", "late", [], [c.idx(2012, 1)]),
                               fl.make_source("AGAGE", "early", [], [c.idx(2009, 1)])]
        self.assertEqual(ge.score(months({}), src, EVENT)["outcome"], "not testable")

    def test_3_sources_tested_both_labs_no_flags_is_a_miss(self):
        r = ge.score(months({}), sources(2, 1), EVENT)
        self.assertEqual((r["outcome"], r["tested_noaa"], r["tested_agage"]), ("miss", 2, 1))

    def test_cfc11_dates_give_a_lead_of_54_months(self):
        event = {"gas": "CFC-11", "group": "CFC-11", "began": "2013-01", "public": "2018-05-16"}
        r = ge.score(months({c.idx(2013, 11): 3}, first=c.idx(2012, 1), last=c.idx(2018, 5)),
                     sources(first=c.idx(2012, 1), last=c.idx(2018, 5)), event)
        self.assertEqual((r["outcome"], r["first_level_3"], r["lead_months"]), ("hit", "2013-11", 54))

    def test_quiet_gas_years_count_only_months_with_possible_true(self):
        ms = months({}, first=c.idx(2008, 1), last=c.idx(2011, 12))
        for m in ms:
            m["possible"] = m["month"] >= c.idx(2008, 7)
        r = ge.score(ms, sources(), EVENT)  # quiet = 2008-01 to 2009-12 = 24 months, 18 possible
        self.assertEqual((r["quiet_months"], r["quiet_months_possible"], r["quiet_gas_years"]), (24, 18, 1.5))

    def test_groups_in_the_event_table(self):
        groups = {e["gas"]: e["group"] for e in ge.EVENTS}
        self.assertEqual(groups, {"HCFC-141b": "HCFC-141b", "CFC-115": "CFC-115",
                                  "CFC-12": "CFC-11", "carbon tetrachloride": "CFC-11"})
        self.assertEqual([e["gas"] for e in ge.EVENTS], [x[0] for x in ge.EVENT_GASES])


def span(first, last, level=3):
    return {i: level for i in range(first, last + 1)}


class CarryOver(unittest.TestCase):
    """A level 3 that carries on from the month before the change began is not a hit."""

    def test_level_3_from_the_month_before_through_the_6th_month_then_0_is_a_miss(self):
        r = scored(span(c.idx(2009, 12), c.idx(2010, 6)))
        self.assertEqual((r["outcome"], r["false_alarm"], r["first_false_level_3"]), ("miss", True, "2009-12"))

    def test_the_same_with_level_3_again_after_a_dip_is_a_hit_at_the_later_month(self):
        levels = span(c.idx(2009, 12), c.idx(2010, 6))
        levels[c.idx(2010, 9)] = 3
        r = scored(levels)
        self.assertEqual((r["outcome"], r["first_level_3"], r["lead_months"], r["false_alarm"]),
                         ("hit", "2010-09", 4, True))

    def test_level_3_from_the_month_before_to_the_end_of_the_stretch_is_a_miss(self):
        r = scored(span(c.idx(2009, 12), c.idx(2010, 12)))
        self.assertEqual((r["outcome"], r["false_alarm"]), ("miss", True))

    def test_level_2_before_and_level_3_in_the_month_it_began_is_a_hit_with_no_false_alarm(self):
        r = scored({c.idx(2009, 12): 2, c.idx(2010, 1): 3})
        self.assertEqual((r["outcome"], r["first_level_3"], r["false_alarm"]), ("hit", "2010-01", False))

    def test_level_3_in_the_first_month_of_the_list_inside_the_stretch_is_a_hit(self):
        r = ge.score(months({c.idx(2010, 1): 3}, first=c.idx(2010, 1)), sources(), EVENT)
        self.assertEqual((r["outcome"], r["first_level_3"]), ("hit", "2010-01"))

    def test_level_3_dips_to_2_and_returns_the_hit_is_the_first_one(self):
        r = scored({c.idx(2010, 4): 3, c.idx(2010, 5): 2, c.idx(2010, 6): 3})
        self.assertEqual((r["outcome"], r["first_level_3"]), ("hit", "2010-04"))


class ThroughTheLadder(unittest.TestCase):
    """The same rule through the real ladder, on CFC-12's dates, 2 NOAA and 1 AGAGE tested every month."""

    FIRST, LAST = c.idx(2005, 1), c.idx(2021, 12)

    def score_flags(self, flag_months):
        """flag_months: one (year, month) for each of the 3 sources."""
        tested = range(self.FIRST, self.LAST + 1)
        src = [fl.make_source(lab, code, [c.idx(*d)], tested)
               for (lab, code), d in zip((("NOAA", "brw"), ("NOAA", "mlo"), ("AGAGE", "mhd")), flag_months)]
        event = next(e for e in ge.EVENTS if e["gas"] == "CFC-12")
        return ge.score(fl.ladder(src, self.FIRST, self.LAST), src, event)

    def test_all_3_flag_in_december_2012_is_a_miss_and_a_false_alarm(self):
        r = self.score_flags([(2012, 12)] * 3)
        self.assertEqual((r["outcome"], r["false_alarm"], r["first_false_level_3"]), ("miss", True, "2012-12"))

    def test_all_3_flag_in_february_2012_is_a_miss_and_a_false_alarm(self):
        r = self.score_flags([(2012, 2)] * 3)
        self.assertEqual((r["outcome"], r["false_alarm"], r["first_false_level_3"]), ("miss", True, "2012-02"))

    def test_all_3_flag_in_january_2012_is_a_miss_and_a_false_alarm(self):
        r = self.score_flags([(2012, 1)] * 3)
        self.assertEqual((r["outcome"], r["false_alarm"], r["first_false_level_3"]), ("miss", True, "2012-01"))

    def test_all_3_flag_in_june_2013_is_a_hit_with_lead_92_and_no_false_alarm(self):
        r = self.score_flags([(2013, 6)] * 3)
        self.assertEqual((r["outcome"], r["first_level_3"], r["lead_months"], r["false_alarm"]),
                         ("hit", "2013-06", 92, False))

    def test_2_flag_in_december_2012_and_the_third_in_february_2013_is_a_hit_with_lead_96(self):
        r = self.score_flags([(2012, 12), (2012, 12), (2013, 2)])
        self.assertEqual((r["outcome"], r["first_level_3"], r["lead_months"], r["false_alarm"]),
                         ("hit", "2013-02", 96, False))


class Gaps(unittest.TestCase):
    def test_5_sources_tested_all_agage_is_not_testable(self):
        r = ge.score(months({c.idx(2010, 6): 3}), sources(0, 5), EVENT)
        self.assertEqual((r["outcome"], r["tested_noaa"], r["tested_agage"]), ("not testable", 0, 5))

    def test_a_third_source_tested_only_in_the_month_the_change_began_counts(self):
        src = sources(1, 1) + [fl.make_source("NOAA", "third", [], [c.idx(2010, 1)])]
        self.assertEqual(ge.score(months({}), src, EVENT)["outcome"], "miss")

    def test_a_third_source_tested_only_in_the_public_month_does_not_count(self):
        src = sources(1, 1) + [fl.make_source("NOAA", "third", [], [c.idx(2011, 1)])]
        self.assertEqual(ge.score(months({}), src, EVENT)["outcome"], "not testable")

    def test_level_2_in_the_quiet_stretch_is_no_false_alarm(self):
        r = scored({c.idx(2009, 5): 2, c.idx(2009, 6): 2})
        self.assertEqual((r["false_alarm"], r["first_false_level_3"]), (False, None))

    def test_first_level_3_month_with_count_5_reports_5_sources(self):
        ms = months({c.idx(2010, 6): 3})
        for m in ms:
            if m["month"] == c.idx(2010, 6):
                m["count"] = 5
        r = ge.score(ms, sources(), EVENT)
        self.assertEqual(r["sources_at_first_level_3"], 5)

    def test_events_are_exactly_the_4_rows_of_issue_25(self):
        self.assertEqual([(e["gas"], e["group"], e["began"], e["public"]) for e in ge.EVENTS], [
            ("HCFC-141b", "HCFC-141b", "2017-01", "2022-04-27"),
            ("CFC-115", "CFC-115", "2011-01", "2017-10-10"),
            ("CFC-12", "CFC-11", "2013-01", "2021-02-10"),
            ("carbon tetrachloride", "CFC-11", "2013-01", "2021-02-10")])
        self.assertTrue(all(set(e) == {"gas", "group", "began", "public"} for e in ge.EVENTS))

    def test_event_gases_are_exactly_the_4_rows_of_issue_25(self):
        self.assertEqual(list(ge.EVENT_GASES), [
            ("HCFC-141b", "HCFC141B_GCMS_flask.txt", "gcms", "hcfc-141b"),
            ("CFC-115", "CFC115_M2.txt", "gcms", "cfc-115"),
            ("CFC-12", "HATS_global_F12.txt", "table:F12", "cfc-12"),
            ("carbon tetrachloride", "HATS_global_CCl4.txt", "table:CCl4", "ccl4")])

    def test_closing_lines_on_made_up_rows(self):
        rows = [{"outcome": "hit", "group": "A", "quiet_months_possible": 50, "false_alarm": False},
                {"outcome": "miss", "group": "B", "quiet_months_possible": 0, "false_alarm": False},
                {"outcome": "not testable", "group": "C", "quiet_months_possible": 20, "false_alarm": True},
                {"outcome": "miss", "group": "C", "quiet_months_possible": 30, "false_alarm": False}]
        self.assertEqual(tuple(ge.closing_lines(rows)), (
            "hits 1, misses 2, not testable 1 of 4 gases, which are 3 separate events",
            "false alarms 1 of 3 gases where level 3 was possible in the quiet stretch"))


def table_lines(tag, stations=NOAA_CODES):
    names = [f"HATS_{tag}_YYYY", f"HATS_{tag}_MM"]
    for agg in ("NH", "SH", "Global"):
        names += [f"HATS_{agg}_{tag}", f"HATS_{agg}_{tag}_sd"]
    for code in stations:
        names += [f"HATS_{code}_{tag}", f"HATS_{code}_{tag}_sd"]
    names.append(f"HATS_{tag}_Programs")
    rows = []
    for i in range(c.idx(2000, 1), c.idx(2000, 6) + 1):
        y, m = c.ym(i)
        rows.append("  ".join([str(y), str(m)] + ["1.000", "0.100"] * 3 + ["2.000", "0.100"] * len(stations) + ["1"]))
    return ["# made up"] * 3 + ["  ".join(names)] + rows, names


class Readers(Base):
    def test_a_cfc115_style_column_line_with_spaces_inside_names_reads(self):
        head = "site\tdec_date\tyyyymmdd hhmmss\tWind Dir.\tWind Spd\tCFC115\tCFC115_sd"
        rows = ["alt\t2010.04\t20100115 123000\tnd\tnd\t8.5\t0.1", "alt\t2010.05\t20100120 123000\tnd\tnd\t9.5\t0.1"]
        p = self.file("cfc115.txt", ['07--Apr-26\t"note"', head] + rows)
        self.assertEqual(g.read_gcms(p), {"alt": {c.idx(2010, 1): 9.0}})

    def check_table(self, tag):
        lines, names = table_lines(tag)
        self.assertEqual(len(names), 33)
        d = g.read_table(self.file(f"{tag}.txt", lines), tag)
        self.assertEqual(sorted(d), sorted(NOAA_CODES))
        self.assertEqual(len(d), 12)
        self.assertEqual(set(d["alt"].values()), {2.0})  # not the 1.000 of NH, SH or Global
        for key in ("NH", "SH", "Global", "Programs"):
            self.assertNotIn(key.lower(), d)
            self.assertNotIn(key, d)

    def test_read_table_with_tag_f12_gives_12_stations(self):
        self.check_table("F12")

    def test_read_table_with_tag_ccl4_gives_12_stations(self):
        self.check_table("CCl4")

    def test_plain_table_still_reads_mc(self):
        p = self.dir / "t.txt"
        write_table(p, {code: straight() for code in NOAA_CODES})
        self.assertEqual(sorted(g.read_table(p)), sorted(NOAA_CODES))
        self.assertEqual(sorted(g.noaa_data(self.dir, "t.txt", "table")), sorted(NOAA_CODES))

    def test_table_kind_with_a_tag_goes_to_that_tag(self):
        lines, _ = table_lines("CCl4")
        self.file("c.txt", lines)
        self.assertEqual(len(g.noaa_data(self.dir, "c.txt", "table:CCl4")), 12)

    def test_a_table_without_the_tags_year_column_stops(self):
        lines, _ = table_lines("F12")
        self.file("c.txt", lines)
        with self.assertRaises(SystemExit):
            g.noaa_data(self.dir, "c.txt", "table:CCl4")


class EndToEnd(Base):
    def test_a_jump_at_2_noaa_and_1_agage_inside_the_stretch_is_a_hit(self):
        noaa_dir, agage_dir, out = self.dir / "noaa", self.dir / "agage", self.dir / "out"
        noaa_dir.mkdir()
        agage_dir.mkdir()
        j = c.idx(2010, 6) - FROM
        write_table(noaa_dir / "HATS_global_MC.txt",
                    {code: straight(k, jump_at=j if code in ("alt", "brw") else None) for k, code in enumerate(NOAA_CODES)})
        for k, code in enumerate(AGAGE_CODES):
            fn = straight(k + 3, jump_at=j if code == "mhd" else None)
            write_nc(agage_dir / f"agage_{code}_ch3ccl3_monthly-baseline-20260716.nc", monthly_rows(fn))
        event = {"gas": MC[0], "group": "made-up", "began": "2010-01", "public": "2011-01-15"}
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rows = ge.run(noaa_dir, agage_dir, out, [MC], [event])
        self.assertEqual(rows[0]["outcome"], "hit")
        self.assertEqual(rows[0]["first_level_3"], "2010-06")
        self.assertEqual(buf.getvalue().strip().splitlines()[-2:],
                         ["hits 1, misses 0, not testable 0 of 1 gases, which are 1 separate events",
                          "false alarms 0 of 1 gases where level 3 was possible in the quiet stretch"])
        for name in ("checks.csv", "sources.csv", "months.csv", "by_year.csv", "summary.csv", "events.csv"):
            self.assertTrue((out / name).exists(), name)
        with open(out / "events.csv", newline="") as fh:
            reader = csv.DictReader(fh)
            row = next(reader)
        self.assertEqual(reader.fieldnames, ge.COLUMNS)
        self.assertEqual((row["outcome"], row["lead_months"], row["false_alarm"]), ("hit", "7", "false"))


if __name__ == "__main__":
    unittest.main()
