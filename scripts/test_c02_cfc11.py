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


if __name__ == "__main__":
    unittest.main()
