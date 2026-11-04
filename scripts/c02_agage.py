#!/usr/bin/env python3
"""AGAGE cross-check for case C02: does the rule from issue 18 see the 2013 CFC-11 slowdown at AGAGE stations?

Data: AGAGE CFC-11 NetCDF files (monthly baseline for six stations, high frequency for Gosan).

Usage:
  python scripts/c02_agage.py <folder holding the files> [--out cases/C02]

Writes agage.csv and agage.json to the out folder.
Standard library, matplotlib and scipy.io.netcdf_file only. The rule is c02_cfc11.roll(), unchanged.
A month with no reading stays no reading: nothing is filled, interpolated or averaged across a gap.
"""
import argparse
import csv
import datetime
import json
import math
import sys
from pathlib import Path

from scipy.io import netcdf_file

sys.path.insert(0, str(Path(__file__).resolve().parent))
import c02_cfc11 as c  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FILL = -9999.0
EPOCH = datetime.datetime(1970, 1, 1)
LONG = [("mhd", "Mace Head"), ("thd", "Trinidad Head"), ("rpb", "Ragged Point"),
        ("smo", "Cape Matatula"), ("cgo", "Cape Grim")]
GOSAN_WINDOW = 60
MIN_TESTED = 12  # fewer tested months than this before 2013, or from 2013, means "not testable"
FIELDS = ["code", "name", "testable", "tested", "tested_before_2013", "tested_from_2013", "skipped",
          "false_alarms_before_2013", "first_flag", "first_flag_from_2013", "months_before_paper",
          "total_flags", "largest_multiple_before_2013", "reading", "excess", "line_value", "gap",
          "usual_miss", "threshold", "multiple"]


def month_of(seconds):
    d = EPOCH + datetime.timedelta(seconds=float(seconds))
    return c.idx(d.year, d.month)


def read_nc(path):
    """-> (list of month index, list of float or None). Fill value and nan become None."""
    nc = netcdf_file(str(path), "r", mmap=False)
    try:
        times = [float(t) for t in nc.variables["time"][:]]
        values = [float(v) for v in nc.variables["mf"][:]]
    finally:
        nc.close()
    return [month_of(t) for t in times], [None if v != v or v == FILL else v for v in values]


def read_monthly(path):
    """{month index: value or None}. One row per month; a later duplicate month is ignored."""
    out = {}
    for i, v in zip(*read_nc(path)):
        out.setdefault(i, v)
    return out


def read_monthly_means(path):
    """High frequency file -> {month index: mean of that month's readings, or None if it has none}."""
    groups = {}
    for i, v in zip(*read_nc(path)):
        groups.setdefault(i, [])
        if v is not None:
            groups[i].append(v)
    return {i: (math.fsum(g) / len(g) if g else None) for i, g in groups.items()}


def excess_of(means, baseline):
    """Month's mean minus that month's baseline; no reading if either is missing."""
    out = {}
    for i in means.keys() | baseline.keys():
        a, b = means.get(i), baseline.get(i)
        out[i] = None if a is None or b is None else a - b
    return out


def find(folder, pattern):
    hits = sorted(Path(folder).glob(pattern))
    if not hits:
        sys.exit(f"no file matching {pattern} in {folder}")
    return hits[-1]


def long_record(code, name, data):
    reading = data.get
    last = max(data)
    recs = [c.roll(reading, i) for i in range(c.idx(2005, 1), last + 1)]
    row = c.summarise(code, name, None, reading, recs)
    tested = [r for r in recs if not r["skipped"]]
    before = sum(r["month"] < "2013-01" for r in tested)
    first = next((r["month"] for r in tested if r["flag"]), None)
    out = {"code": code, "name": name, "tested_before_2013": before, "tested_from_2013": len(tested) - before,
           "first_flag": first}
    out["testable"] = before >= MIN_TESTED and len(tested) - before >= MIN_TESTED
    for k in FIELDS:
        if k in row:
            out[k] = row[k]
    return out, recs


def gosan_record(means, baseline):
    ex = excess_of(means, baseline)
    have = [i for i, v in ex.items() if v is not None]
    if not have:
        sys.exit("Gosan has no month with both a monthly mean and a baseline")
    start, last = min(have) + GOSAN_WINDOW, max(ex)
    recs = [c.roll(ex.get, i, GOSAN_WINDOW) for i in range(start, last + 1)]
    row = c.summarise("gsn", "Gosan", None, ex.get, recs)
    flags = [r for r in recs if r["flag"]]
    out = {"code": "gsn", "name": "Gosan", "tested": row["tested"], "skipped": row["skipped"],
           "first_flag": flags[0]["month"] if flags else None,
           "first_flag_from_2013": row["first_flag_from_2013"], "total_flags": row["total_flags"],
           "excess": None, "line_value": None, "gap": None, "usual_miss": None, "threshold": None, "multiple": None}
    if flags:
        f = flags[0]
        out.update({"excess": ex[c.idx(int(f["month"][:4]), int(f["month"][5:]))], "line_value": f["line_value"],
                    "gap": f["gap"], "usual_miss": f["usual_miss"], "threshold": f["threshold"],
                    "multiple": c.multiple_of(f)})
    return out, recs


def confirmation(rows):
    """Count of long-record stations that are testable, have a first flag from 2013 before May 2018, and 0 false alarms before 2013."""
    n = sum(1 for r in rows if r["testable"] and r["false_alarms_before_2013"] == 0
            and r["first_flag_from_2013"] is not None and r["first_flag_from_2013"] < "2018-05")
    return n >= 3, n


def run(folder, out):
    stations = []
    for code, name in LONG:
        path = find(folder, f"agage_{code}_cfc-11_monthly-baseline-*.nc")
        stations.append(long_record(code, name, read_monthly(path)))
    baseline = read_monthly(find(folder, "agage_gsn_cfc-11_monthly-baseline-*.nc"))
    means = read_monthly_means(find(folder, "agage_gsn_cfc-11_[0-9]*.nc"))
    gosan = gosan_record(means, baseline)
    rows = [r for r, _ in stations]
    ok, n = confirmation(rows)

    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    everyone = stations + [gosan]
    (out / "agage.json").write_text(
        json.dumps({"stations": [dict(r, months=m) for r, m in everyone],
                    "confirmation": {"met": ok, "count": n, "of": len(rows)}},
                   indent=1, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    with open(out / "agage.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(FIELDS)
        for r, _ in everyone:
            w.writerow(["" if r.get(k) is None else repr(r[k]) if isinstance(r[k], float) else r[k] for k in FIELDS])

    for r, _ in everyone:
        if r.get("testable") is False:
            print(f"{r['code']} {r['name']}: NOT TESTABLE (tested {r['tested']}, before 2013 {r['tested_before_2013']}, "
                  f"from 2013 {r['tested_from_2013']}, skipped {r['skipped']}; first flag from 2013 {r['first_flag_from_2013']})")
        else:
            print(f"{r['code']} {r['name']}: tested {r['tested']}, skipped {r['skipped']}, "
                  f"false alarms before 2013 {r.get('false_alarms_before_2013')}, first flag {r['first_flag']}, "
                  f"first flag from 2013 {r['first_flag_from_2013']}, total flags {r['total_flags']}, multiple {r['multiple']}")
    print(f"confirmation (at least 3 of 5 flag from 2013 before May 2018 with 0 false alarms before 2013): "
          f"{'yes' if ok else 'no'}, {n} of {len(rows)}")
    return {"stations": [r for r, _ in everyone], "months": {r["code"]: m for r, m in everyone},
            "confirmation": (ok, n)}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("folder", help="folder holding the AGAGE .nc files")
    ap.add_argument("--out", default=str(ROOT / "cases" / "C02"))
    args = ap.parse_args()
    run(args.folder, args.out)


if __name__ == "__main__":
    main()
