"""Tests for scripts/c02_cfc11.py. Made-up data only, written to a temp folder."""
import contextlib
import io
import json
import random
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import c02_cfc11 as c  # noqa: E402

HEADER = ["# made-up file in the shape of NOAA's", "#  Date: 2026-01-01",
          "#  Calibration scale used:  TEST 2000", "#"]


def build(folder, fn, end=(2018, 12)):
    """fn(t) gives the reading for month t, t counted in months from Jan 1995 (None for nan)."""
    lines = HEADER + ["HATS_F11_YYYY HATS_F11_MM HATS_NH_F11 HATS_Global_F11"]
    for i in range(c.idx(1995, 1), c.idx(*end) + 1):
        y, m = c.ym(i)
        v = fn(i - c.idx(1995, 1))
        lines.append(f"{y} {m:02d} 1.0 {'nan' if v is None else repr(v)}")
    path = Path(folder) / "made_up.txt"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def build_stations(folder, stations, south=None, end=(2018, 12)):
    """NOAA's shape with north, south, global and the given stations (code -> fn). Two made-up station comment lines."""
    south = south or (lambda t: 100.0 - 1.0 * t / 12)
    codes = list(stations)
    head = HEADER + ["#  aaa = Alpha Point, Testland (12.5N, 10.0W) (flask only)",
                     "#  bbb = South Base (90S)(flask and in insitu)", "#  nan = not a number or no data"]
    cols = ["HATS_NH_F11", "HATS_NH_F11_sd", "HATS_SH_F11", "HATS_SH_F11_sd", "HATS_Global_F11"] + \
           [x for k in codes for x in (f"HATS_{k}_F11", f"HATS_{k}_F11_sd")]
    lines = head + ["HATS_F11_YYYY HATS_F11_MM " + " ".join(cols) + " HATS_F11_Programs"]
    cell = lambda v: "nan" if v is None else repr(v)
    for i in range(c.idx(1995, 1), c.idx(*end) + 1):
        y, m = c.ym(i)
        t = i - c.idx(1995, 1)
        vals = [260.0 - t / 12, 0.1, south(t), 0.1, 255.0 - t / 12]
        for k in codes:
            vals += [stations[k](t), 0.1]
        lines.append(f"{y} {m:02d} " + " ".join(cell(v) for v in vals) + " 100000")
    path = Path(folder) / "made_up_stations.txt"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def run(path, out):
    with contextlib.redirect_stdout(io.StringIO()):
        return c.run(path, out)


class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def test_1_exact_line(self):
        path = build(self.dir, lambda t: 260.0 - 2.0 * t / 12)
        tr = run(path, self.dir / "out")
        for p in tr["q1"]["periods"]:
            self.assertAlmostEqual(p["slope"], -2.0, places=9)
        for r in tr["q2"]:
            self.assertAlmostEqual(r["usual_miss"], 0.0, places=8)
        self.assertEqual(tr["ingest"]["file_date"], "2026-01-01")
        self.assertEqual(tr["ingest"]["calibration_scale"], "TEST 2000")

    def test_2_steady_fall_small_noise_no_flags(self):
        rng = random.Random(1)
        path = build(self.dir, lambda t: 260.0 - 2.0 * t / 12 + rng.uniform(-0.05, 0.05))
        tr = run(path, self.dir / "out")
        self.assertEqual(tr["summary"]["total_flags"], 0)
        self.assertEqual(tr["summary"]["outcome"], "no flag before May 2018")

    def test_3_fall_halves(self):
        rng = random.Random(2)
        brk = c.idx(2010, 1) - c.idx(1995, 1)

        def f(t):
            base = -2.0 * t / 12 if t <= brk else -2.0 * brk / 12 - 1.0 * (t - brk) / 12
            return 260.0 + base + rng.uniform(-0.05, 0.05)

        tr = run(build(self.dir, f), self.dir / "out")
        s = tr["summary"]
        self.assertIsNotNone(s["first_flag"])
        self.assertGreater(s["first_flag"], "2010-01")
        self.assertEqual([r["month"] for r in tr["q2"] if r["flag"] and r["month"] <= "2010-01"], [])

    def test_4_nan_in_window_skips(self):
        nan_t = c.idx(2000, 6) - c.idx(1995, 1)
        path = build(self.dir, lambda t: None if t == nan_t else 260.0 - 2.0 * t / 12)
        tr = run(path, self.dir / "out")
        skipped = [r["month"] for r in tr["q2"] if r["skipped"]]
        # 2000-06 sits in the 120-month window of every month from 2005-01 to 2010-06
        self.assertEqual(skipped[0], "2005-01")
        self.assertEqual(skipped[-1], "2010-06")
        self.assertEqual(tr["summary"]["skips"], len(skipped))
        self.assertIn("2000-06", tr["q2"][0]["skip_reason"])
        self.assertEqual(tr["ingest"]["nan_months"], ["2000-06"])

    def test_5_byte_identical(self):
        rng = random.Random(3)
        vals = [260.0 - 2.0 * t / 12 + rng.uniform(-0.3, 0.3) for t in range(30 * 12)]
        path = build(self.dir, lambda t: vals[t])
        run(path, self.dir / "a")
        run(path, self.dir / "b")
        self.assertEqual((self.dir / "a" / "trace.json").read_bytes(), (self.dir / "b" / "trace.json").read_bytes())
        self.assertEqual((self.dir / "a" / "check.csv").read_bytes(), (self.dir / "b" / "check.csv").read_bytes())
        json.loads((self.dir / "a" / "trace.json").read_text())

    def test_6_station_names_and_latitudes(self):
        got = c.parse_stations([
            "#  kum = Cape Kumukahi, Hawaii, USA (19.5N, 154.8W) (flask only)",
            "#  smo = Cape Matatula, American Samoa (14.3S, 170.6W)(flask and in insitu)",
            "#  spo = South Pole (90S)(flask and in insitu)",
            "#  oldGC = Original flask program started in 1977",
            "#  nan = not a number or no data"])
        self.assertEqual(got, {"kum": ("Cape Kumukahi, Hawaii, USA", 19.5),
                               "smo": ("Cape Matatula, American Samoa", -14.3),
                               "spo": ("South Pole", -90.0)})
        path = build_stations(self.dir, {"aaa": lambda t: 260.0 - 2.0 * t / 12, "bbb": lambda t: 260.0 - 2.0 * t / 12})
        rows = {r["series"]: r for r in run(path, self.dir / "out")["all_series"]}
        self.assertEqual((rows["aaa"]["name"], rows["aaa"]["lat"]), ("Alpha Point, Testland", 12.5))
        self.assertEqual((rows["bbb"]["name"], rows["bbb"]["lat"]), ("South Base", -90.0))
        self.assertIsNone(rows["north"]["lat"])

    def test_7_earlier_halving_flags_earlier(self):
        def halves_at(year, month, seed):
            rng = random.Random(seed)
            brk = c.idx(year, month) - c.idx(1995, 1)
            return lambda t: 260.0 + (-2.0 * t / 12 if t <= brk else -2.0 * brk / 12 - 1.0 * (t - brk) / 12) + rng.uniform(-0.05, 0.05)

        path = build_stations(self.dir, {"aaa": halves_at(2013, 6, 4), "bbb": halves_at(2015, 6, 5)})
        tr = run(path, self.dir / "out")
        rows = {r["series"]: r for r in tr["all_series"]}
        a, b = rows["aaa"]["first_flag_from_2013"], rows["bbb"]["first_flag_from_2013"]
        self.assertIsNotNone(a)
        self.assertIsNotNone(b)
        self.assertLess(a, b)
        self.assertGreater(a, "2013-06")
        self.assertEqual(rows["aaa"]["false_alarms_before_2013"], 0)
        self.assertEqual(rows["aaa"]["months_before_paper"], c.idx(2018, 5) - c.idx(int(a[:4]), int(a[5:])))
        self.assertEqual(rows["bbb"]["months_before_paper"], c.idx(2018, 5) - c.idx(int(b[:4]), int(b[5:])))
        order = [r["series"] for r in tr["all_series"] if r["first_flag_from_2013"]]
        self.assertLess(order.index("aaa"), order.index("bbb"))
        self.assertEqual(tr["all_series"][-1]["first_flag_from_2013"], None)

    def test_8_north_minus_south(self):
        got = c.north_minus_south({0: 5.0, 1: 7.0, 2: None, 3: 9.0}, {0: 2.0, 1: None, 2: 1.0})
        self.assertEqual(got, {0: 3.0, 1: None, 2: None, 3: None})
        nan_t = c.idx(2000, 6) - c.idx(1995, 1)
        path = build_stations(self.dir, {}, south=lambda t: None if t == nan_t else 100.0 - 1.0 * t / 12)
        rows = {r["series"]: r for r in run(path, self.dir / "out")["all_series"]}
        self.assertEqual(rows["north_minus_south"]["skipped"], 66)  # 2005-01 to 2010-06, as in test 4
        self.assertEqual(rows["north"]["skipped"], 0)
        self.assertEqual(rows["south"]["skipped"], 66)
        yearly = {y["year"]: y for y in run(path, self.dir / "out2")["north_south_yearly"]}
        self.assertEqual(yearly[2000]["months"], 11)
        self.assertEqual(yearly[2001]["months"], 12)
        self.assertEqual(max(yearly), 2018)

    def test_9_worth_a_look_skips_false_alarms(self):
        def row(sid, false_alarms, first, months):
            return {"series": sid, "name": sid, "lat": None, "false_alarms_before_2013": false_alarms,
                    "first_flag_from_2013": first, "months_before_paper": months, "reading": 1.0, "line_value": 1.0,
                    "gap": 1.0, "usual_miss": 1.0, "threshold": 3.0, "multiple": 1.0}
        rows = [row("a", 2, "2013-01", 64), row("b", 0, "2014-03", 50), row("c", 0, "2014-03", 50),
                row("d", 0, "2016-01", 28), row("e", 0, None, None)]
        got = c.pick_worth(rows)
        self.assertEqual(got["month"], "2014-03")
        self.assertEqual(got["months_before_paper"], 50)
        self.assertEqual([r["series"] for r in got["series"]], ["b", "c"])
        self.assertIsNone(c.pick_worth([row("a", 1, "2013-01", 64)]))
        # through the whole program: aaa flags before 2013 and again from 2013, bbb is clean and later
        def halves_at(year, seed, month=1):
            rng = random.Random(seed)
            brk = c.idx(year, month) - c.idx(1995, 1)
            return lambda t: 260.0 + (-2.0 * t / 12 if t <= brk else -2.0 * brk / 12 - 1.0 * (t - brk) / 12) + rng.uniform(-0.05, 0.05)
        path = build_stations(self.dir, {"aaa": halves_at(2011, 6, 6), "bbb": halves_at(2015, 7)})
        tr = run(path, self.dir / "out")
        rows = {r["series"]: r for r in tr["all_series"]}
        self.assertGreater(rows["aaa"]["false_alarms_before_2013"], 0)
        self.assertEqual(rows["bbb"]["false_alarms_before_2013"], 0)
        self.assertLess(rows["aaa"]["first_flag_from_2013"], rows["bbb"]["first_flag_from_2013"])
        self.assertEqual([r["series"] for r in tr["worth_a_look"]["series"]], ["bbb"])
        self.assertEqual(tr["worth_a_look"]["month"], rows["bbb"]["first_flag_from_2013"])


if __name__ == "__main__":
    unittest.main()
