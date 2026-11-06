"""Tests for scripts/clean_gases.py. Made-up files only, written to temp folders."""
import contextlib
import csv
import datetime
import io
import sys
import tempfile
import unittest
from pathlib import Path

from scipy.io import netcdf_file

sys.path.insert(0, str(Path(__file__).resolve().parent))
import c02_agage as a  # noqa: E402
import c02_cfc11 as c  # noqa: E402
import clean_gases as g  # noqa: E402

FROM = c.idx(1995, 1)
END = c.idx(2018, 12)
MC = ("methyl chloroform", "HATS_global_MC.txt", "table", "ch3ccl3")
NOAA_CODES = "alt brw sum mhd thd nwr kum smo cgo psa spo hfm".split()  # hfm is outside the 18
AGAGE_CODES = "mhd thd rpb smo cgo".split()
PATTERN = [0.0, 0.03, -0.03, 0.05, -0.05, 0.02, -0.02]  # a small fixed up and down, so a straight fall is not exact


def straight(shift=0, jump_at=None, jump=5.0):
    """Reading for month t (months from Jan 1995): a steady fall plus the fixed pattern, and one optional jump."""
    def fn(t):
        v = 260.0 - 2.0 * t / 12 + PATTERN[(t + shift) % 7]
        return v + jump if t == jump_at else v
    return fn


def seconds(y, m, day=15):
    return (datetime.datetime(y, m, day) - datetime.datetime(1970, 1, 1)).total_seconds()


def write_nc(path, rows):
    """rows: list of (year, month, day, value)."""
    nc = netcdf_file(str(path), "w")
    nc.createDimension("time", len(rows))
    t = nc.createVariable("time", "d", ("time",))
    t[:] = [seconds(y, m, d) for y, m, d, _ in rows]
    t.units = "seconds since 1970-01-01 00:00:00"
    mf = nc.createVariable("mf", "d", ("time",))
    mf[:] = [a.FILL if v is None else v for _, _, _, v in rows]
    mf._FillValue = a.FILL
    nc.close()


def monthly_rows(fn, first=FROM, end=END):
    rows = []
    for i in range(first, end + 1):
        y, m = c.ym(i)
        rows.append((y, m, 15, fn(i - FROM)))
    return rows


def hf_rows(baseline_fn, excess_fn, first, end):
    rows = []
    for i in range(first, end + 1):
        y, m = c.ym(i)
        mid = baseline_fn(i - FROM) + excess_fn(i - FROM)
        rows += [(y, m, 5, mid - 0.7), (y, m, 20, mid + 0.7)]
    return rows


def write_table(path, series, end=END):
    """series: {code: fn(t) -> value or None}. The 33 column layout of the combined table."""
    names = ["HATS_MC_YYYY", "HATS_MC_MM"]
    for agg in ("NH", "SH", "Global"):
        names += [f"HATS_{agg}_MC", f"HATS_{agg}_MC_sd"]
    for code in series:
        names += [f"HATS_{code}_MC", f"HATS_{code}_MC_sd"]
    names.append("HATS_MC_Programs")
    lines = ["# made up header line"] * 5 + ["  ".join(names)]
    for i in range(FROM, end + 1):
        y, m = c.ym(i)
        row = [str(y), str(m)] + ["1.000", "0.100"] * 3
        for fn in series.values():
            v = fn(i - FROM)
            row += ["nan" if v is None else f"{v:.6f}", "0.100"]
        row.append("1")
        lines.append("  ".join(row))
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return names


GCMS_NOTE = '07--Apr-26\t"NOAA/ESRL/GMD flask data, supplied for collaborative use"'
GCMS_HEAD = "site\tdec_date\tyyyymmdd hhmmss\twind_dir\twind_spd\tHAL1211\tHAL1211_sd"
H1301_HEAD = " site      decdate    yyyymmdd    HH:MM   wind_dir   wind_spd         H-1301_C      H-1301_sd     flag   instr."


def gcms_row(site, day="20100115", value="9.5", dec="2010.04", time="123000"):
    return f"{site}\t{dec}\t{day} {time}\tnd\tnd\t{value}\t0.1"


def h1301_row(site, value, instr, day="20100115", hhmm="12:30", flag="-"):
    return f"  {site} 2010.0400000    {day}    {hhmm}        999       9.99            {value}     0.10000000        {flag}      {instr}"


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def file(self, name, lines):
        p = self.dir / name
        p.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return p


class Readers(Base):
    def gcms(self, rows):
        return g.read_gcms(self.file("gcms.txt", [GCMS_NOTE, GCMS_HEAD] + rows))

    def h1301(self, rows):
        return g.read_h1301(self.file("h1301.txt", ["# comment"] * 26 + [H1301_HEAD] + rows))

    def test_note_and_column_lines_are_skipped(self):
        d = self.gcms([gcms_row("alt", value="9.5"), gcms_row("alt", day="20100120", value="10.5")])
        self.assertEqual(d, {"alt": {c.idx(2010, 1): 10.0}})

    def test_lower_and_upper_case_sites_come_out_the_same(self):
        d = self.gcms([gcms_row("alt", value="9.0"), gcms_row("ALT", day="20100120", value="11.0")])
        self.assertEqual(list(d), ["alt"])
        self.assertEqual(d["alt"][c.idx(2010, 1)], 10.0)
        d = self.h1301([h1301_row("ALT", "3.0", "PR1")])
        self.assertEqual(list(d), ["alt"])

    def test_mlo_pfp_is_averaged_in_with_mlo(self):
        d = self.gcms([gcms_row("mlo", value="10.0"), gcms_row("mlo_pfp", day="20100120", value="20.0")])
        self.assertEqual(list(d), ["mlo"])
        self.assertEqual(d["mlo"][c.idx(2010, 1)], 15.0)

    def test_both_instruments_on_one_sample_keeps_pr1(self):
        d = self.h1301([h1301_row("ALT", "10.0", "M2"), h1301_row("ALT", "20.0", "PR1")])
        self.assertEqual(d["alt"][c.idx(2010, 1)], 20.0)

    def test_an_m2_row_with_no_partner_stays(self):
        d = self.h1301([h1301_row("ALT", "10.0", "M2", hhmm="09:00"), h1301_row("ALT", "20.0", "PR1")])
        self.assertEqual(d["alt"][c.idx(2010, 1)], 15.0)

    def test_a_pr1_row_with_no_partner_stays(self):
        d = self.h1301([h1301_row("ALT", "10.0", "M2"), h1301_row("ALT", "20.0", "PR1", hhmm="09:00")])
        self.assertEqual(d["alt"][c.idx(2010, 1)], 15.0)
        d = self.h1301([h1301_row("ALT", "20.0", "PR1", hhmm="09:00")])
        self.assertEqual(d["alt"][c.idx(2010, 1)], 20.0)

    def test_a_flag_other_than_dash_stops_with_an_error(self):
        with self.assertRaises(SystemExit):
            self.h1301([h1301_row("ALT", "10.0", "PR1", flag="*")])

    def test_a_mole_fraction_that_is_not_a_number_stops_with_an_error(self):
        with self.assertRaises(SystemExit):
            self.gcms([gcms_row("alt", value="nd")])
        with self.assertRaises(SystemExit):
            self.gcms([gcms_row("alt", value="nan")])
        with self.assertRaises(SystemExit):
            self.h1301([h1301_row("ALT", "nd", "PR1")])

    def test_a_sample_on_31_january_stays_in_january(self):
        d = self.gcms([gcms_row("alt", day="20100131", dec="2010.0875", value="9.0"),
                       gcms_row("alt", day="20100201", dec="2010.09", value="12.0")])
        self.assertEqual(d["alt"], {c.idx(2010, 1): 9.0, c.idx(2010, 2): 12.0})
        d = self.gcms([gcms_row("alt", day="20100131", dec="2010.9999", value="9.0")])
        self.assertEqual(list(d["alt"]), [c.idx(2010, 1)])

    def test_a_month_with_no_sample_has_no_reading(self):
        d = self.gcms([gcms_row("alt", day="20100115"), gcms_row("alt", day="20100315")])
        self.assertNotIn(c.idx(2010, 2), d["alt"])
        self.assertIsNone(d["alt"].get(c.idx(2010, 2)))

    def test_nan_in_the_combined_table_is_no_reading(self):
        p = self.dir / "t.txt"
        write_table(p, {code: (lambda t: None if t == 30 else 1.0) for code in NOAA_CODES})
        d = g.read_table(p)
        self.assertNotIn(FROM + 30, d["alt"])
        self.assertIn(FROM + 31, d["alt"])

    def test_the_combined_table_gives_exactly_12_stations(self):
        p = self.dir / "t.txt"
        names = write_table(p, {code: straight() for code in NOAA_CODES})
        self.assertEqual(len(names), 33)
        d = g.read_table(p)
        self.assertEqual(sorted(d), sorted(NOAA_CODES))
        self.assertEqual(len(d), 12)


class EndToEnd(Base):
    def setUp(self):
        super().setUp()
        self.noaa, self.agage, self.out = self.dir / "noaa", self.dir / "agage", self.dir / "out"
        self.noaa.mkdir()
        self.agage.mkdir()

    def go(self, noaa=None, agage=None, extra=None, printed=None):
        """noaa: {code: fn}; agage: {code: fn or rows}. Defaults are straight falls everywhere. printed: a buffer for the output."""
        noaa = noaa or {code: straight(k) for k, code in enumerate(NOAA_CODES)}
        agage = agage or {code: straight(k + 3) for k, code in enumerate(AGAGE_CODES)}
        write_table(self.noaa / "HATS_global_MC.txt", noaa)
        for code, fn in agage.items():
            rows = fn if isinstance(fn, list) else monthly_rows(fn)
            write_nc(self.agage / f"agage_{code}_ch3ccl3_monthly-baseline-20260716.nc", rows)
        for name, rows in (extra or {}).items():
            write_nc(self.agage / name, rows)
        with contextlib.redirect_stdout(printed or io.StringIO()):
            result = g.run(self.noaa, self.agage, self.out, [MC])
        return result["gases"][0]

    @staticmethod
    def by_label(gas):
        return {c.label(m["month"]): m for m in gas["months"]}

    def summary(self):
        with open(self.out / "summary.csv", newline="") as fh:
            return next(csv.DictReader(fh))

    @staticmethod
    def jumped(codes, month, shift=0, names=None):
        """Straight falls for `names`, with a one-month jump at `codes` in `month`."""
        j = month - FROM
        names = NOAA_CODES if names is None else names
        return {code: straight(k + shift, jump_at=j if code in codes else None) for k, code in enumerate(names)}

    def test_level_3_inside_the_18_counts_on_both_pass_lines(self):
        month, buf = c.idx(2010, 6), io.StringIO()
        self.go(noaa=self.jumped(("alt", "brw"), month),
                agage=self.jumped(("mhd",), month, 3, AGAGE_CODES), printed=buf)
        self.assertEqual(buf.getvalue().strip().splitlines()[-3:],
                         ["gases reaching level 3: 1 of 1",
                          "gases reaching level 3 on the CFC-11 set: 1 of 1",
                          "gosan flagged on: none"])

    def test_level_3_outside_the_18_counts_only_on_the_first_pass_line(self):
        month, buf = c.idx(2010, 6), io.StringIO()
        agage = self.jumped((), month, 3, AGAGE_CODES)
        agage["jfj"] = straight(1, jump_at=month - FROM)
        agage["cmn"] = straight(2, jump_at=month - FROM)
        self.go(noaa=self.jumped(("hfm",), month), agage=agage, printed=buf)
        self.assertEqual(buf.getvalue().strip().splitlines()[-3:-1],
                         ["gases reaching level 3: 1 of 1",
                          "gases reaching level 3 on the CFC-11 set: 0 of 1"])

    def test_a_gosan_flag_is_named_on_the_last_line(self):
        first, end, month = c.idx(2008, 1), c.idx(2014, 12), c.idx(2013, 6)
        base = straight()
        excess = lambda t: 1.0 + 0.01 * PATTERN[t % 7] + (5.0 if t == month - FROM else 0.0)  # noqa: E731
        extra = {"agage_gsn_ch3ccl3_monthly-baseline-20260716.nc": monthly_rows(base, first, end),
                 "agage_gsn_ch3ccl3_20260716.nc": hf_rows(base, excess, first, end)}
        buf = io.StringIO()
        gas = self.go(extra=extra, printed=buf)
        self.assertEqual(buf.getvalue().strip().splitlines()[-1], "gosan flagged on: methyl chloroform")
        self.assertEqual(min(gas["gosan"].flags), month)
        self.assertEqual(self.summary()["gosan_first_flag"], "2013-06")

    def test_gosan_without_its_high_frequency_file_stops_with_an_error(self):
        extra = {"agage_gsn_ch3ccl3_monthly-baseline-20260716.nc": monthly_rows(straight(), c.idx(2008, 1), c.idx(2014, 12))}
        with self.assertRaises(SystemExit):
            self.go(extra=extra)

    def test_level_3_runs_leave_out_a_level_2_run(self):
        first, second = c.idx(2010, 6), c.idx(2014, 6)
        noaa = {code: straight(k) for k, code in enumerate(NOAA_CODES)}
        for code in ("alt", "brw"):
            noaa[code] = straight(NOAA_CODES.index(code), jump_at=first - FROM)
        for code in ("kum", "nwr"):
            noaa[code] = straight(NOAA_CODES.index(code), jump_at=second - FROM)
        self.go(noaa=noaa, agage=self.jumped(("mhd",), first, 3, AGAGE_CODES))
        row = self.summary()
        self.assertEqual((row["level_3_runs"], row["months_level_3plus"], row["months_level_2"]), ("1", "12", "12"))

    def test_gas_years_count_only_months_where_level_3_was_possible(self):
        late = {code: monthly_rows(straight(k + 3), first=c.idx(2003, 1)) for k, code in enumerate(AGAGE_CODES)}
        self.go(agage=late)  # AGAGE reaches 108 of 120 window months in January 2012
        row = self.summary()
        self.assertEqual((row["months_run"], row["months_possible"]), ("168", "84"))
        self.assertEqual(float(row["gas_years"]), 7.0)

    def test_straight_falls_everywhere_stay_at_level_0(self):
        gas = self.go()
        self.assertEqual({m["level"] for m in gas["months"]}, {0})
        self.assertEqual(sum(len(s.flags) for s in gas["sources"]), 0)
        self.assertGreater(sum(len(s.tested) for s in gas["sources"]), 2000)
        self.assertEqual(len(gas["sources"]), 17)

    def test_a_one_month_jump_at_one_source_is_level_1_for_12_months(self):
        j = c.idx(2010, 6) - FROM
        noaa = {code: straight(k, jump_at=j if code == "alt" else None) for k, code in enumerate(NOAA_CODES)}
        gas = self.go(noaa=noaa)
        months = self.by_label(gas)
        self.assertEqual([m["level"] for m in gas["months"] if m["level"]], [1] * 12)
        self.assertEqual(months["2010-06"]["level"], 1)
        self.assertEqual(months["2011-05"]["level"], 1)
        self.assertEqual(months["2011-06"]["level"], 0)
        self.assertEqual(months["2010-05"]["level"], 0)

    def test_a_jump_at_3_noaa_sources_and_no_agage_stays_level_2(self):
        j = c.idx(2010, 6) - FROM
        noaa = {code: straight(k, jump_at=j if code in ("alt", "brw", "mhd") else None) for k, code in enumerate(NOAA_CODES)}
        gas = self.go(noaa=noaa)
        self.assertEqual(max(m["level"] for m in gas["months"]), 2)
        self.assertTrue(self.by_label(gas)["2010-06"]["one_lab_3plus"])

    def test_a_jump_at_2_noaa_and_1_agage_is_level_3(self):
        j = c.idx(2010, 6) - FROM
        noaa = {code: straight(k, jump_at=j if code in ("alt", "brw") else None) for k, code in enumerate(NOAA_CODES)}
        agage = {code: straight(k + 3, jump_at=j if code == "mhd" else None) for k, code in enumerate(AGAGE_CODES)}
        gas = self.go(noaa=noaa, agage=agage)
        m = self.by_label(gas)["2010-06"]
        self.assertEqual((m["level"], m["count"], m["possible"]), (3, 3, True))
        self.assertEqual(max(x["level"] for x in gas["months"]), 3)

    def test_a_jump_at_10_sources_in_both_labs_and_both_hemispheres_is_level_4(self):
        j = c.idx(2010, 6) - FROM
        hit_noaa = ("alt", "brw", "mhd", "nwr", "kum", "spo", "cgo")
        hit_agage = ("mhd", "thd", "cgo")
        noaa = {code: straight(k, jump_at=j if code in hit_noaa else None) for k, code in enumerate(NOAA_CODES)}
        agage = {code: straight(k + 3, jump_at=j if code in hit_agage else None) for k, code in enumerate(AGAGE_CODES)}
        gas = self.go(noaa=noaa, agage=agage)
        m = self.by_label(gas)["2010-06"]
        self.assertEqual((m["count"], m["level"]), (10, 4))

    def test_a_jump_only_outside_the_18_leaves_level_18_at_0(self):
        j = c.idx(2010, 6) - FROM
        noaa = {code: straight(k, jump_at=j if code == "hfm" else None) for k, code in enumerate(NOAA_CODES)}
        agage = {code: straight(k + 3) for k, code in enumerate(AGAGE_CODES)}
        agage["jfj"] = straight(1, jump_at=j)
        agage["cmn"] = straight(2, jump_at=j)
        gas = self.go(noaa=noaa, agage=agage)
        m = self.by_label(gas)["2010-06"]
        self.assertEqual((m["level"], m["count"]), (3, 3))
        self.assertEqual({x["level_18"] for x in gas["months"]}, {0})
        self.assertEqual({x["count_18"] for x in gas["months"]}, {0})

    def test_a_record_ending_in_1990_is_listed_with_0_tested(self):
        old = monthly_rows(straight(), first=c.idx(1985, 1), end=c.idx(1990, 12))
        gas = self.go(agage={**{code: straight(k) for k, code in enumerate(AGAGE_CODES)}, "old": old})
        s = next(s for s in gas["sources"] if s.id == "AGAGE old")
        self.assertEqual((len(s.tested), len(s.flags)), (0, 0))
        with open(self.out / "sources.csv", newline="") as fh:
            row = next(r for r in csv.DictReader(fh) if r["source"] == "AGAGE old")
        self.assertEqual((row["tested"], row["flags"], row["first_flag"]), ("0", "0", ""))

    def test_gosan_gets_its_own_shorter_window(self):
        first, end = c.idx(2008, 1), c.idx(2014, 12)
        base, excess = straight(), (lambda t: 1.0 + 0.01 * PATTERN[t % 7])
        extra = {"agage_gsn_ch3ccl3_monthly-baseline-20260716.nc": monthly_rows(base, first, end),
                 "agage_gsn_ch3ccl3_20260716.nc": hf_rows(base, excess, first, end)}
        gas = self.go(extra=extra)
        gs = gas["gosan"]
        self.assertIsNotNone(gs)
        self.assertEqual(min(gs.tested), c.idx(2013, 1))  # 60 months after the first month with a reading
        self.assertEqual(max(gs.tested), end)
        self.assertEqual(len(gs.tested), 24)
        with open(self.out / "checks.csv", newline="") as fh:
            rows = [r for r in csv.DictReader(fh) if r["source"] == "AGAGE gsn"]
        self.assertEqual(rows[0]["month"], "2013-01")
        self.assertEqual(len(rows), 24)  # nothing before 2013, where a 10 year rule would still have needed to start

    def test_a_gap_over_10_percent_of_a_window_skips_those_months_and_fills_nothing(self):
        gap = range(c.idx(2008, 1) - FROM, c.idx(2008, 1) - FROM + 30)

        def holey(t):
            return None if t in gap else straight()(t)
        noaa = {code: straight(k) for k, code in enumerate(NOAA_CODES)}
        noaa["alt"] = holey
        gas = self.go(noaa=noaa)
        s = next(s for s in gas["sources"] if s.id == "NOAA alt")
        self.assertNotIn(c.idx(2008, 1), s.tested)           # the month itself has no reading
        self.assertNotIn(c.idx(2012, 1), s.tested)           # 30 of its 120 window months have none
        self.assertIn(c.idx(2007, 12), s.tested)             # before the gap it tests as usual
        with open(self.out / "checks.csv", newline="") as fh:
            rows = {r["month"]: r for r in csv.DictReader(fh) if r["source"] == "NOAA alt"}
        self.assertEqual(rows["2008-01"]["reading"], "")     # absent, never 0
        self.assertEqual(rows["2008-01"]["skipped"], "true")
        self.assertEqual(rows["2012-01"]["skipped"], "true")
        self.assertIn("only", rows["2012-01"]["skip_reason"])
        self.assertEqual(rows["2012-01"]["flag"], "skipped")
        self.assertEqual(rows["2009-01"]["reading"], "")

    def test_the_five_csv_files_are_written(self):
        self.go()
        for name in ("checks.csv", "sources.csv", "months.csv", "by_year.csv", "summary.csv"):
            self.assertTrue((self.out / name).exists(), name)
        with open(self.out / "summary.csv", newline="") as fh:
            row = next(csv.DictReader(fh))
        self.assertEqual(row["gas"], "methyl chloroform")
        self.assertEqual(row["top_level"], "0")
        self.assertEqual(row["sources_listed"], "17")

    def test_the_last_lines_are_counts_and_months_only(self):
        write_table(self.noaa / "HATS_global_MC.txt", {code: straight() for code in NOAA_CODES})
        for code in AGAGE_CODES:
            write_nc(self.agage / f"agage_{code}_ch3ccl3_monthly-baseline-20260716.nc", monthly_rows(straight()))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            g.run(self.noaa, self.agage, self.out, [MC])
        last = buf.getvalue().strip().splitlines()[-3:]
        self.assertEqual(last, ["gases reaching level 3: 0 of 1",
                                "gases reaching level 3 on the CFC-11 set: 0 of 1",
                                "gosan flagged on: none"])


if __name__ == "__main__":
    unittest.main()
