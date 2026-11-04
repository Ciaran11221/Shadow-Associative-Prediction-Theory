"""Tests for scripts/c02_agage.py. Made-up NetCDF files only, written to a temp folder."""
import contextlib
import datetime
import io
import json
import math
import random
import sys
import tempfile
import unittest
from pathlib import Path

from scipy.io import netcdf_file

sys.path.insert(0, str(Path(__file__).resolve().parent))
import c02_agage as a  # noqa: E402
import c02_cfc11 as c  # noqa: E402

FROM = c.idx(1995, 1)


def seconds(y, m, day=15):
    return (datetime.datetime(y, m, day) - datetime.datetime(1970, 1, 1)).total_seconds()


def write_nc(path, rows):
    """rows: list of (year, month, day, value or None). None is written as the fill value."""
    nc = netcdf_file(str(path), "w")
    nc.createDimension("time", len(rows))
    t = nc.createVariable("time", "d", ("time",))
    t[:] = [seconds(y, m, d) for y, m, d, _ in rows]
    t.units = "seconds since 1970-01-01 00:00:00"
    t.calendar = "proleptic_gregorian"
    mf = nc.createVariable("mf", "f", ("time",))
    mf[:] = [a.FILL if v is None else v for _, _, _, v in rows]
    mf.units = "ppt"
    mf._FillValue = a.FILL
    nc.close()


def monthly_rows(fn, skip=(), fill=(), end=(2018, 12)):
    """fn(t): reading, t in months from Jan 1995. skip: t with no row at all. fill: t written as the fill value."""
    rows = []
    for i in range(FROM, c.idx(*end) + 1):
        t = i - FROM
        if t in skip:
            continue
        y, m = c.ym(i)
        rows.append((y, m, 15, None if t in fill else fn(t)))
    return rows


def halves_at(year, month, seed):
    rng = random.Random(seed)
    brk = c.idx(year, month) - FROM
    return lambda t: 260.0 + (-2.0 * t / 12 if t <= brk else -2.0 * brk / 12 - 1.0 * (t - brk) / 12) + rng.uniform(-0.05, 0.05)


def steady(seed):
    rng = random.Random(seed)
    return lambda t: 260.0 - 2.0 * t / 12 + rng.uniform(-0.05, 0.05)


def hf_rows(baseline_fn, excess_fn, end=(2018, 12)):
    """Two readings a month, a day apart, whose mean is baseline + excess."""
    rows = []
    for i in range(FROM, c.idx(*end) + 1):
        t = i - FROM
        y, m = c.ym(i)
        mid = baseline_fn(t) + excess_fn(t)
        rows += [(y, m, 5, mid - 0.7), (y, m, 20, mid + 0.7)]
    return rows


class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def test_1_monthly_file_reads_back_and_fill_is_no_reading(self):
        path = self.dir / "m.nc"
        write_nc(path, [(2000, 1, 15, 250.5), (2000, 2, 15, None), (2000, 3, 15, 249.25), (2000, 5, 15, 248.0)])
        got = a.read_monthly(path)
        self.assertEqual(sorted(got), [c.idx(2000, 1), c.idx(2000, 2), c.idx(2000, 3), c.idx(2000, 5)])
        self.assertEqual(got[c.idx(2000, 1)], 250.5)
        self.assertIsNone(got[c.idx(2000, 2)])  # the fill value
        self.assertEqual(got[c.idx(2000, 3)], 249.25)
        self.assertIsNone(got.get(c.idx(2000, 4)))  # no row at all stays no reading
        # a nan in the file is also no reading
        write_nc(path, [(2000, 1, 15, float("nan")), (2000, 2, 15, 1.0)])
        self.assertIsNone(a.read_monthly(path)[c.idx(2000, 1)])
        # month labels come from the time variable, for a date at the very start and end of a month
        write_nc(path, [(1999, 12, 31, 1.0), (2000, 1, 1, 2.0)])
        self.assertEqual(a.read_monthly(path), {c.idx(1999, 12): 1.0, c.idx(2000, 1): 2.0})

    def test_2_halving_in_2013_flags_after_and_no_false_alarms(self):
        path = self.dir / "m.nc"
        write_nc(path, monthly_rows(halves_at(2013, 1, 7)))
        row, recs = a.long_record("mhd", "Mace Head", a.read_monthly(path))
        self.assertEqual(row["false_alarms_before_2013"], 0)
        self.assertIsNotNone(row["first_flag_from_2013"])
        self.assertGreater(row["first_flag_from_2013"], "2013-01")
        self.assertEqual(row["first_flag"], row["first_flag_from_2013"])
        self.assertEqual(row["months_before_paper"], c.idx(2018, 5) - c.idx(int(row["first_flag"][:4]), int(row["first_flag"][5:])))
        self.assertTrue(row["testable"])
        self.assertEqual(row["skipped"], 0)
        self.assertEqual(row["tested"], len(recs))
        self.assertEqual(recs[0]["month"], "2005-01")
        self.assertEqual(recs[0]["window_first"], "1995-01")  # the 120-month window
        self.assertGreater(row["multiple"], 3)
        self.assertAlmostEqual(row["threshold"], 3 * row["usual_miss"], places=12)
        self.assertGreater(row["gap"], row["threshold"])
        # a steady fall with the same noise never flags
        write_nc(path, monthly_rows(steady(8)))
        row, _ = a.long_record("mhd", "Mace Head", a.read_monthly(path))
        self.assertEqual((row["total_flags"], row["first_flag"], row["first_flag_from_2013"]), (0, None, None))

    def test_3_gap_in_window_skips_and_is_never_filled(self):
        gap_t = c.idx(2000, 6) - FROM
        for kind in ("fill", "absent"):
            path = self.dir / f"{kind}.nc"
            rows = monthly_rows(steady(9), **({"fill": {gap_t}} if kind == "fill" else {"skip": {gap_t}}))
            write_nc(path, rows)
            data = a.read_monthly(path)
            row, recs = a.long_record("cgo", "Cape Grim", data)
            skipped = [r["month"] for r in recs if r["skipped"]]
            self.assertEqual((skipped[0], skipped[-1]), ("2005-01", "2010-06"))
            self.assertEqual(row["skipped"], 66)  # 2000-06 sits in the window of every month 2005-01 to 2010-06
            self.assertEqual(row["tested"] + row["skipped"], len(recs))
            self.assertIn("2000-06", recs[0]["skip_reason"])
            self.assertIsNone(data.get(c.idx(2000, 6)))  # still no reading afterwards
            self.assertIsNone(recs[0]["slope"])
        # a gap that is the month itself skips only that month
        path = self.dir / "own.nc"
        own = c.idx(2015, 3) - FROM
        write_nc(path, monthly_rows(steady(10), fill={own}))
        row, recs = a.long_record("cgo", "Cape Grim", a.read_monthly(path))
        self.assertEqual([r["month"] for r in recs if r["skipped"]][0], "2015-03")
        self.assertEqual(row["skipped"], c.idx(2018, 12) - c.idx(2015, 3) + 1)  # 2015-03 and every month after it, to the end of the file

    def test_4_gosan_excess_and_60_month_window(self):
        base = steady(11)
        b = {t: base(t) for t in range(c.idx(2018, 12) - FROM + 1)}
        rng = random.Random(12)
        brk = c.idx(2010, 1) - FROM
        exc = {t: (2.0 if t < brk else 5.0) + rng.uniform(-0.05, 0.05) for t in b}
        write_nc(self.dir / "b.nc", monthly_rows(lambda t: b[t]))
        write_nc(self.dir / "h.nc", hf_rows(lambda t: b[t], lambda t: exc[t]))
        baseline, means = a.read_monthly(self.dir / "b.nc"), a.read_monthly_means(self.dir / "h.nc")
        ex = a.excess_of(means, baseline)
        t0 = c.idx(2003, 4) - FROM
        self.assertAlmostEqual(ex[FROM + t0], exc[t0], places=3)  # mean of the month's two readings minus its baseline
        self.assertAlmostEqual(means[FROM + t0] - baseline[FROM + t0], ex[FROM + t0], places=12)
        row, recs = a.gosan_record(means, baseline)
        self.assertEqual(recs[0]["month"], "2000-01")  # first month with 60 months before it
        self.assertEqual(recs[0]["window_first"], "1995-01")
        self.assertEqual(recs[0]["window_last"], "1999-12")
        self.assertEqual(recs[-1]["month"], "2018-12")
        self.assertEqual(recs[0]["n"], 60)
        self.assertEqual(row["tested"], len(recs))
        self.assertEqual(row["skipped"], 0)
        self.assertGreaterEqual(row["first_flag"], "2010-01")
        self.assertAlmostEqual(row["excess"], 5.0, delta=0.1)
        self.assertGreater(row["gap"], row["threshold"])
        # a month missing from either side is no reading, and so is a month whose high-frequency readings are all fill
        self.assertEqual(a.excess_of({1: 5.0, 2: 6.0, 3: None, 4: 8.0}, {1: 2.0, 2: None, 3: 1.0}),
                         {1: 3.0, 2: None, 3: None, 4: None})
        write_nc(self.dir / "h2.nc", [(2000, 1, 5, None), (2000, 1, 6, None), (2000, 2, 5, 3.0), (2000, 2, 6, 5.0)])
        self.assertEqual(a.read_monthly_means(self.dir / "h2.nc"), {c.idx(2000, 1): None, c.idx(2000, 2): 4.0})
        # the cfc11 default window is untouched
        self.assertEqual(c.roll(lambda j: 1.0, c.idx(2005, 1))["window_first"], "1995-01")

    def test_5_confirmation_counts_clean_early_flags(self):
        def row(false_alarms, first, testable=True):
            return {"testable": testable, "false_alarms_before_2013": false_alarms, "first_flag_from_2013": first}
        good = row(0, "2016-03")
        self.assertEqual(a.confirmation([good, good, good, row(0, None), row(0, "2019-01")]), (True, 3))
        self.assertEqual(a.confirmation([good, good, row(0, None), row(0, None), row(0, "2018-05")]), (False, 2))
        # a station with a false alarm does not count: 3 flags, one with a false alarm, is only 2
        self.assertEqual(a.confirmation([good, good, row(1, "2014-01"), row(0, None), row(0, None)]), (False, 2))
        self.assertEqual(a.confirmation([good, good, good, row(1, "2014-01"), row(0, None)]), (True, 3))
        # a station that cannot be tested does not count
        self.assertEqual(a.confirmation([good, good, row(0, "2014-01", testable=False), row(0, None), row(0, None)]), (False, 2))

    def test_6_too_few_tested_months_is_not_testable(self):
        path = self.dir / "m.nc"
        write_nc(path, monthly_rows(steady(13), fill=set(range(c.idx(2000, 1) - FROM, c.idx(2018, 12) - FROM + 1, 6))))
        row, _ = a.long_record("thd", "Trinidad Head", a.read_monthly(path))
        self.assertFalse(row["testable"])
        self.assertEqual(row["tested"], 0)
        self.assertEqual(row["skipped"], c.idx(2018, 12) - c.idx(2005, 1) + 1)

    def test_7_whole_run_writes_files_deterministically(self):
        data = self.dir / "data"
        data.mkdir()
        fns = {"mhd": halves_at(2013, 6, 21), "thd": halves_at(2014, 6, 22), "rpb": halves_at(2015, 6, 23),
               "smo": steady(24), "cgo": steady(25)}
        for code, fn in fns.items():
            write_nc(data / f"agage_{code}_cfc-11_monthly-baseline-20260716.nc", monthly_rows(fn))
        base = steady(26)
        b = {t: base(t) for t in range(c.idx(2018, 12) - FROM + 1)}
        write_nc(data / "agage_gsn_cfc-11_monthly-baseline-20260716.nc", monthly_rows(lambda t: b[t]))
        write_nc(data / "agage_gsn_cfc-11_20260716.nc", hf_rows(lambda t: b[t], lambda t: 1.0))
        outs = []
        for name in ("a", "b"):
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                res = a.run(data, self.dir / name)
            outs.append(buf.getvalue())
        self.assertEqual(outs[0], outs[1])
        for f in ("agage.csv", "agage.json"):
            self.assertEqual((self.dir / "a" / f).read_bytes(), (self.dir / "b" / f).read_bytes())
        self.assertEqual(res["confirmation"], (True, 3))
        self.assertIn("confirmation", outs[0].splitlines()[-1])
        self.assertIn("yes, 3 of 5", outs[0].splitlines()[-1])
        self.assertEqual(len(outs[0].splitlines()), 7)
        self.assertEqual(len((self.dir / "a" / "agage.csv").read_text().splitlines()), 7)  # header and six stations
        self.assertEqual([r["code"] for r in res["stations"]], ["mhd", "thd", "rpb", "smo", "cgo", "gsn"])


    # ---- the gap rule: min_share 0.9, set on issue 18 ----

    def test_8_one_gap_in_window_first_rule_skips_gap_rule_tests_with_n_119(self):
        path = self.dir / "m.nc"
        write_nc(path, monthly_rows(steady(31), fill={c.idx(2000, 6) - FROM}))
        data = a.read_monthly(path)
        first, first_recs = a.long_record("cgo", "Cape Grim", data)
        gaps, gap_recs = a.long_record("cgo", "Cape Grim", data, a.GAP_SHARE)
        self.assertTrue(first_recs[0]["skipped"])  # 2005-01 has 2000-06 in its window
        self.assertFalse(gap_recs[0]["skipped"])
        self.assertEqual(gap_recs[0]["month"], "2005-01")
        self.assertEqual(gap_recs[0]["n"], 119)  # the missing month is not counted and not filled
        self.assertEqual((first["skipped"], gaps["skipped"]), (66, 0))
        self.assertEqual(gaps["tested"], len(gap_recs))
        self.assertIsNone(data.get(c.idx(2000, 6)))  # still no reading afterwards
        # months whose window is full give exactly the same record under both rules
        full = [(x, y) for x, y in zip(first_recs, gap_recs) if not x["skipped"]]
        self.assertTrue(full)
        for x, y in full:
            self.assertEqual(x, y)

    def test_9_thirteen_gaps_in_a_window_skip_twelve_test(self):
        path = self.dir / "m.nc"
        write_nc(path, monthly_rows(steady(32), skip=set(range(0, 13))))  # 1995-01 to 1996-01 have no row
        _, recs = a.long_record("mhd", "Mace Head", a.read_monthly(path), a.GAP_SHARE)
        self.assertEqual(recs[0]["month"], "2005-01")  # window 1995-01 to 2004-12: 13 gaps, 107 of 120
        self.assertTrue(recs[0]["skipped"])
        self.assertIn("107 of 120", recs[0]["skip_reason"])
        self.assertEqual(recs[1]["month"], "2005-02")  # window 1995-02 to 2005-01: 12 gaps, 108 of 120
        self.assertFalse(recs[1]["skipped"])
        self.assertEqual(recs[1]["n"], 108)
        self.assertEqual(recs[2]["n"], 109)

    def test_10_gap_in_the_month_itself_is_skipped_under_both_rules(self):
        path = self.dir / "m.nc"
        write_nc(path, monthly_rows(steady(33), fill={c.idx(2015, 3) - FROM}))
        data = a.read_monthly(path)
        for share in (1.0, a.GAP_SHARE):
            _, recs = a.long_record("cgo", "Cape Grim", data, share)
            rec = next(r for r in recs if r["month"] == "2015-03")
            self.assertTrue(rec["skipped"])
            self.assertEqual(rec["skip_reason"], "no reading for 2015-03")
        # under the gap rule only that month goes; the next one has a full window but one gap
        _, recs = a.long_record("cgo", "Cape Grim", data, a.GAP_SHARE)
        self.assertEqual([r["month"] for r in recs if r["skipped"]], ["2015-03"])
        self.assertEqual(next(r for r in recs if r["month"] == "2015-04")["n"], 119)

    def test_11_gosan_window_needs_54_of_60(self):
        def gosan(gaps, share):
            means = {FROM + t: 2.0 + 0.01 * t for t in range(61) if t not in gaps}
            return a.gosan_record(means, {FROM + t: 0.0 for t in range(61)}, share)
        _, recs = gosan(set(range(1, 7)), a.GAP_SHARE)  # 6 gaps in the window of 2000-01
        self.assertEqual(recs[0]["month"], "2000-01")
        self.assertFalse(recs[0]["skipped"])
        self.assertEqual(recs[0]["n"], 54)
        _, recs = gosan(set(range(1, 8)), a.GAP_SHARE)  # 7 gaps: 53 of 60
        self.assertTrue(recs[0]["skipped"])
        self.assertIn("53 of 60", recs[0]["skip_reason"])
        # the first rule skips even one gap
        _, recs = gosan({3}, 1.0)
        self.assertTrue(recs[0]["skipped"])
        _, recs = gosan({3}, a.GAP_SHARE)
        self.assertEqual(recs[0]["n"], 59)

    def test_12_line_through_existing_months_matches_hand_worked_case(self):
        # window 4, min_share 0.75 -> 3 of 4 needed. Months t=0,1,3 exist (t=2 missing), readings 10, 13, 15; month t=4 reads 20.
        # mean t = 4/3, mean y = 38/3, Sxx = 14/3, Sxy = 22/3, slope = 11/7 per month.
        # line: t=0 -> 74/7, t=1 -> 85/7, t=3 -> 107/7, t=4 -> 118/7. Misses -4/7, 6/7, -2/7: usual miss = sqrt((16+36+4)/49/3) = sqrt(8/21).
        base = c.idx(2010, 1)
        vals = {base: 10.0, base + 1: 13.0, base + 3: 15.0, base + 4: 20.0}
        rec = c.roll(vals.get, base + 4, 4, 0.75)
        self.assertFalse(rec["skipped"])
        self.assertEqual(rec["n"], 3)
        self.assertAlmostEqual(rec["slope"], 12 * 11 / 7, places=9)  # x is in years, so float rounding in the dates shows from the 12th place
        self.assertAlmostEqual(rec["line_value"], 118 / 7, places=9)
        self.assertAlmostEqual(rec["gap"], 20 - 118 / 7, places=9)
        self.assertAlmostEqual(rec["usual_miss"], math.sqrt(8 / 21), places=9)
        self.assertAlmostEqual(rec["threshold"], 3 * math.sqrt(8 / 21), places=9)
        self.assertTrue(rec["flag"])  # 22/7 = 3.14 against 3 x 0.617 = 1.85
        # the default and an explicit 1.0 skip it, and nothing is filled
        for rec in (c.roll(vals.get, base + 4, 4), c.roll(vals.get, base + 4, 4, 1.0)):
            self.assertTrue(rec["skipped"])
            self.assertEqual(rec["skip_reason"], "no reading for " + c.label(base + 2))
        self.assertIsNone(vals.get(base + 2))
        # only 2 of 4 is not enough
        del vals[base]
        self.assertTrue(c.roll(vals.get, base + 4, 4, 0.75)["skipped"])

    def test_13_whole_run_with_gap_rule_writes_its_own_files(self):
        data = self.dir / "data"
        data.mkdir()
        fns = {"mhd": halves_at(2013, 6, 21), "thd": halves_at(2014, 6, 22), "rpb": halves_at(2015, 6, 23),
               "smo": steady(24), "cgo": steady(25)}
        for code, fn in fns.items():
            write_nc(data / f"agage_{code}_cfc-11_monthly-baseline-20260716.nc",
                     monthly_rows(fn, fill={c.idx(2001, 3) - FROM}))
        base = steady(26)
        b = {t: base(t) for t in range(c.idx(2018, 12) - FROM + 1)}
        write_nc(data / "agage_gsn_cfc-11_monthly-baseline-20260716.nc", monthly_rows(lambda t: b[t]))
        write_nc(data / "agage_gsn_cfc-11_20260716.nc", hf_rows(lambda t: b[t], lambda t: 1.0))
        outs = []
        for name in ("a", "b"):
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                a.run(data, self.dir / name)
                res = a.run(data, self.dir / name, a.GAP_SHARE, "agage_gaps")
            outs.append(buf.getvalue())
        self.assertEqual(outs[0], outs[1])
        for f in ("agage.csv", "agage.json", "agage_gaps.csv", "agage_gaps.json"):
            self.assertEqual((self.dir / "a" / f).read_bytes(), (self.dir / "b" / f).read_bytes())
        first_rows = (self.dir / "a" / "agage.csv").read_text().splitlines()
        gap_rows = (self.dir / "a" / "agage_gaps.csv").read_text().splitlines()
        self.assertEqual(first_rows[0], gap_rows[0])  # same shape
        self.assertEqual(len(gap_rows), 7)
        self.assertEqual(res["confirmation"], (True, 3))
        self.assertEqual(len(outs[0].splitlines()), 14)
        self.assertIn("confirmation", outs[0].splitlines()[6])
        self.assertIn("confirmation", outs[0].splitlines()[-1])
        # 2001-03 is missing: the first rule skips 2005-01 to 2011-03 (75 months) at each long station, the gap rule skips none
        by_code = lambda f: {r["code"]: r for r in json.loads((self.dir / "a" / f).read_text())["stations"]}
        self.assertEqual(by_code("agage.json")["mhd"]["skipped"], 75)
        self.assertEqual(by_code("agage_gaps.json")["mhd"]["skipped"], 0)


if __name__ == "__main__":
    unittest.main()
