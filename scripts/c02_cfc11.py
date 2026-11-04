#!/usr/bin/env python3
"""Check for case C02: does NOAA's global CFC-11 table show the 2013 slowdown early?

Data: NOAA GML HATS global CFC-11, doi:10.15138/BVQ6-2S69

Usage:
  python scripts/c02_cfc11.py <path to NOAA's file> [--out cases/C02]

Writes trace.json, check.csv, all_series.csv and chart.png to the out folder.
Standard library plus matplotlib. Straight lines are ordinary least squares in plain Python.
The rule is fixed: see the Q1 and Q2 sections below.
"""
import argparse
import csv
import hashlib
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOI = "doi:10.15138/BVQ6-2S69"
SOURCE_URL = "https://gml.noaa.gov/aftp/data/hats/cfcs/cfc11/combined/HATS_global_F11.txt"
YEAR_COL, MONTH_COL, GLOBAL_COL = "HATS_F11_YYYY", "HATS_F11_MM", "HATS_Global_F11"
SERIES_START = (1995, 1)
WINDOW = 120
MULTIPLE = 3
DATE = re.compile(r"^#\s*Date:\s*(.+?)\s*$")
SCALE = re.compile(r"^#\s*Calibration scale used:\s*(.+?)\s*$")


def idx(year, month):
    return year * 12 + month - 1


def ym(i):
    return divmod(i, 12)[0], divmod(i, 12)[1] + 1


def label(i):
    y, m = ym(i)
    return f"{y:04d}-{m:02d}"


def xval(i):
    y, m = ym(i)
    return y + (m - 0.5) / 12


def fit(points):
    """points: list of (x, y). OLS with x centred on its mean."""
    n = len(points)
    x_mean = math.fsum(p[0] for p in points) / n
    y_mean = math.fsum(p[1] for p in points) / n
    sxx = math.fsum((p[0] - x_mean) ** 2 for p in points)
    sxy = math.fsum((p[0] - x_mean) * (p[1] - y_mean) for p in points)
    return {"n": n, "slope": sxy / sxx, "x_mean": x_mean, "y_mean": y_mean}


def line_at(f, x):
    return f["y_mean"] + f["slope"] * (x - f["x_mean"])


def ingest(path):
    raw = Path(path).read_bytes()
    lines = raw.decode("utf-8").replace("\r\n", "\n").split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    info = {"source_url": SOURCE_URL, "file_date": None, "calibration_scale": None,
            "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "comment_lines": []}
    names, col, rows, nan_months, dup = None, None, {}, [], []
    first_data = last_data = None
    for number, text in enumerate(lines, 1):
        if text.startswith("#"):
            info["comment_lines"].append({"line_number": number, "text": text})
            m = DATE.match(text)
            if m and info["file_date"] is None:
                info["file_date"] = m.group(1)
            m = SCALE.match(text)
            if m and info["calibration_scale"] is None:
                info["calibration_scale"] = m.group(1)
            continue
        if not text.strip():
            continue
        if names is None:
            names = text.split()
            for need in (YEAR_COL, MONTH_COL, GLOBAL_COL):
                if need not in names:
                    sys.exit(f"column {need} not found; columns are: {names}")
            col = {n: names.index(n) for n in (YEAR_COL, MONTH_COL, GLOBAL_COL)}
            continue
        parts = text.split()
        year, month = int(parts[col[YEAR_COL]]), int(parts[col[MONTH_COL]])
        cell = parts[col[GLOBAL_COL]]
        value = None if cell.lower() == "nan" else float(cell)
        i = idx(year, month)
        if first_data is None:
            first_data = number
        last_data = number
        if i in rows:
            dup.append(label(i))
            continue
        rows[i] = {"reading": value, "line_number": number, "raw_line": text}
        if value is None:
            nan_months.append(label(i))
    if names is None or not rows:
        sys.exit("no data rows found")
    first, last = min(rows), max(rows)
    info.update({
        "column_names": names, "global_column": GLOBAL_COL, "data_rows": len(rows) + len(dup),
        "first_data_line": first_data, "last_data_line": last_data,
        "nan_months": nan_months, "duplicate_months": dup,
        "missing_months": [label(i) for i in range(first, last + 1) if i not in rows],
    })
    return info, rows, last


def roll(reading, i):
    """The rule for month i. reading(j) gives a number, or None for no reading.
    A line through the previous 120 calendar months; skip the month if it or any of its 120 has no reading."""
    rec = {"month": label(i), "window_first": label(i - WINDOW), "window_last": label(i - 1),
           "n": None, "slope": None, "x_mean": None, "y_mean": None, "usual_miss": None,
           "line_value": None, "gap": None, "threshold": None, "flag": False,
           "skipped": False, "skip_reason": None}
    missing = [label(j) for j in range(i - WINDOW, i + 1) if reading(j) is None]
    if missing:
        rec["skipped"] = True
        rec["skip_reason"] = "no reading for " + ", ".join(missing)
    else:
        pts = [(xval(j), reading(j)) for j in range(i - WINDOW, i)]
        f = fit(pts)
        miss = math.sqrt(math.fsum((y - line_at(f, x)) ** 2 for x, y in pts) / len(pts))
        lv = line_at(f, xval(i))
        gap = reading(i) - lv
        rec.update({"n": f["n"], "slope": f["slope"], "x_mean": f["x_mean"], "y_mean": f["y_mean"],
                    "usual_miss": miss, "line_value": lv, "gap": gap,
                    "threshold": MULTIPLE * miss, "flag": gap > MULTIPLE * miss})
    return rec


STATION_LINE = re.compile(r"^#\s*(\w+)\s*=\s*(.+?)\s*$")
LAT = re.compile(r"\(\s*(\d+(?:\.\d+)?)\s*([NS])\b")
COLUMN = re.compile(r"^HATS_(.+)_F11$")
PAPER = idx(2018, 5)


def parse_stations(comment_lines):
    """code -> (name, latitude). Name is the text up to the first ' ('; South is negative."""
    out = {}
    for text in comment_lines:
        m = STATION_LINE.match(text)
        if not m:
            continue
        rest = m.group(2)
        lat = LAT.search(rest)
        if not lat:
            continue
        name = rest.split(" (")[0].strip()
        value = float(lat.group(1)) * (-1 if lat.group(2) == "S" else 1)
        out.setdefault(m.group(1).lower(), (name, value))
    return out


def read_file(path):
    """Whole file: (comment lines, {HATS_*_F11 column: {month index: value or None}}). Later duplicate months are ignored."""
    lines = Path(path).read_bytes().decode("utf-8").replace("\r\n", "\n").split("\n")
    comments, names, cols = [], None, {}
    for text in lines:
        if text.startswith("#"):
            comments.append(text)
            continue
        if not text.strip():
            continue
        parts = text.split()
        if names is None:
            names = parts
            cols = {n: {} for n in names if COLUMN.match(n)}
            continue
        i = idx(int(parts[names.index(YEAR_COL)]), int(parts[names.index(MONTH_COL)]))
        for n, d in cols.items():
            if i not in d:
                cell = parts[names.index(n)]
                d[i] = None if cell.lower() == "nan" else float(cell)
    return comments, cols


def north_minus_south(north, south):
    """Month by month; no reading if either side has none."""
    out = {}
    for i in north.keys() | south.keys():
        a, b = north.get(i), south.get(i)
        out[i] = None if a is None or b is None else a - b
    return out


def multiple_of(rec):
    return rec["gap"] / rec["usual_miss"] if rec["usual_miss"] else None


def run_series(sid, name, lat, reading, last):
    recs = [roll(reading, i) for i in range(idx(2005, 1), last + 1)]
    tested = [r for r in recs if not r["skipped"]]
    flags = [r for r in tested if r["flag"]]
    before = [r for r in flags if r["month"] < "2013-01"]
    early = [multiple_of(r) for r in tested if r["month"] < "2013-01" and multiple_of(r) is not None]
    first = next((r for r in flags if r["month"] >= "2013-01"), None)
    rec = {"series": sid, "name": name, "lat": lat, "tested": len(tested), "skipped": len(recs) - len(tested),
           "false_alarms_before_2013": len(before),
           "first_flag_from_2013": first["month"] if first else None,
           "months_before_paper": PAPER - idx(int(first["month"][:4]), int(first["month"][5:])) if first else None,
           "total_flags": len(flags), "largest_multiple_before_2013": max(early) if early else None}
    for k in ("reading", "line_value", "gap", "usual_miss", "threshold", "multiple"):
        rec[k] = None
    if first:
        i = idx(int(first["month"][:4]), int(first["month"][5:]))
        rec.update({"reading": reading(i), "line_value": first["line_value"], "gap": first["gap"],
                    "usual_miss": first["usual_miss"], "threshold": first["threshold"], "multiple": multiple_of(first)})
    return rec


def pick_worth(all_series):
    """Earliest first flag from 2013 among series with no false alarm before 2013, with every series sharing that month."""
    clean = [r for r in all_series if r["false_alarms_before_2013"] == 0 and r["first_flag_from_2013"]]
    if not clean:
        return None
    month = min(r["first_flag_from_2013"] for r in clean)
    keep = ("series", "name", "lat", "reading", "line_value", "gap", "usual_miss", "threshold", "multiple")
    return {"month": month,
            "months_before_paper": next(r["months_before_paper"] for r in clean if r["first_flag_from_2013"] == month),
            "series": [{k: r[k] for k in keep} for r in clean if r["first_flag_from_2013"] == month]}


def every_series(path, global_reading, last):
    comments, cols = read_file(path)
    stations = parse_stations(comments)
    todo = [("global", "Global", None, global_reading)]
    north, south = cols.get("HATS_NH_F11"), cols.get("HATS_SH_F11")
    if north is not None:
        todo.append(("north", "North", None, north.get))
    if south is not None:
        todo.append(("south", "South", None, south.get))
    diff = None
    if north is not None and south is not None:
        diff = north_minus_south(north, south)
        todo.append(("north_minus_south", "North minus south", None, diff.get))
    for n, d in cols.items():
        code = COLUMN.match(n).group(1)
        if code in ("NH", "SH", "Global"):
            continue
        name, lat = stations.get(code.lower(), (code, None))
        todo.append((code, name, lat, d.get))
    rows = [run_series(sid, name, lat, rd, last) for sid, name, lat, rd in todo]
    rows.sort(key=lambda r: (r["first_flag_from_2013"] is None, r["first_flag_from_2013"] or ""))
    yearly = []
    if diff is not None:
        last_year = ym(last)[0] if ym(last)[1] == 12 else ym(last)[0] - 1
        for y in range(2000, last_year + 1):
            vals = [diff.get(idx(y, m)) for m in range(1, 13)]
            vals = [v for v in vals if v is not None]
            yearly.append({"year": y, "mean": math.fsum(vals) / len(vals) if vals else None, "months": len(vals)})
    return rows, pick_worth(rows), yearly


def run(path, out):
    info, rows, last = ingest(path)
    start = idx(*SERIES_START)

    def reading(i):
        r = rows.get(i)
        return None if r is None else r["reading"]

    series = []
    for i in range(start, last + 1):
        r = rows.get(i)
        series.append({"month": label(i), "x": xval(i), "reading": reading(i),
                       "line_number": r["line_number"] if r else None,
                       "raw_line": r["raw_line"] if r else None})

    # Question 1: two straight lines. Months with no reading are left out of the fit; n says how many were used.
    q1 = {"periods": []}
    for first, last_m in (((2002, 1), (2012, 12)), ((2013, 1), (2017, 12))):
        pts = [(xval(i), reading(i)) for i in range(idx(*first), idx(*last_m) + 1) if reading(i) is not None]
        f = fit(pts) if len(pts) >= 2 else None
        q1["periods"].append({"first_month": label(idx(*first)), "last_month": label(idx(*last_m)),
                              "n": len(pts), "slope": f and f["slope"],
                              "x_mean": f and f["x_mean"], "y_mean": f and f["y_mean"]})
    s1, s2 = q1["periods"][0]["slope"], q1["periods"][1]["slope"]
    q1["percent"] = s2 / s1 * 100 if s1 and s2 is not None else None
    q1["in_band"] = q1["percent"] is not None and 40 <= q1["percent"] <= 60

    # Question 2: for each month, a line through the previous 120 calendar months.
    q2 = [roll(reading, i) for i in range(idx(2005, 1), last + 1)]

    flags = [r["month"] for r in q2 if r["flag"]]
    before_2013 = [m for m in flags if m < "2013-01"]
    from_2013 = [m for m in flags if m >= "2013-01"]
    if not any(m < "2018-05" for m in flags):
        outcome = "no flag before May 2018"
    elif before_2013:
        outcome = "flags before 2013"
    else:
        outcome = "visible early"
    summary = {"first_flag": flags[0] if flags else None, "flags_before_2013": len(before_2013),
               "first_flag_from_2013": from_2013[0] if from_2013 else None, "total_flags": len(flags),
               "skips": sum(r["skipped"] for r in q2), "outcome": outcome}

    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    all_series, worth, yearly = every_series(path, reading, last)
    trace = {"ingest": info, "series": series, "q1": q1, "q2": q2, "summary": summary,
             "all_series": all_series, "worth_a_look": worth, "north_south_yearly": yearly}
    (out / "trace.json").write_text(json.dumps(trace, indent=1, allow_nan=False) + "\n",
                                    encoding="utf-8", newline="\n")
    with open(out / "check.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["month", "reading", "line_value", "usual_miss", "gap", "flag"])
        for r in q2:
            rd = reading(idx(int(r["month"][:4]), int(r["month"][5:])))
            cells = [rd, r["line_value"], r["usual_miss"], r["gap"]]
            w.writerow([r["month"]] + ["" if c is None else repr(c) for c in cells]
                       + ["skipped" if r["skipped"] else str(r["flag"]).lower()])
    with open(out / "all_series.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        keys = list(all_series[0].keys())
        w.writerow(keys)
        for r in all_series:
            w.writerow(["" if r[k] is None else repr(r[k]) if isinstance(r[k], float) else r[k] for k in keys])
    chart(out / "chart.png", rows, q1["periods"][0], last, q2)

    p1, p2 = q1["periods"]
    print(f"slope {p1['first_month']} to {p1['last_month']}: {p1['slope']} ppt per year (n={p1['n']})")
    print(f"slope {p2['first_month']} to {p2['last_month']}: {p2['slope']} ppt per year (n={p2['n']})")
    print(f"second as percent of first: {q1['percent']}  in_band (40 to 60): {q1['in_band']}")
    print(f"first flag month: {summary['first_flag']}")
    print(f"flags before January 2013: {summary['flags_before_2013']}")
    print(f"first flag from January 2013: {summary['first_flag_from_2013']}")
    print(f"total flags: {summary['total_flags']}  skips: {summary['skips']}")
    print(f"outcome: {outcome}")
    if worth:
        print(f"worth a look: {worth['month']}, {worth['months_before_paper']} months before the paper: "
              + ", ".join(r["series"] for r in worth["series"]))
    else:
        print("worth a look: none")
    return trace


def chart(path, rows, p1, last, q2):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    f = {"slope": p1["slope"], "x_mean": p1["x_mean"], "y_mean": p1["y_mean"]}
    months = list(range(idx(2002, 1), last + 1))
    pts = [(xval(i), rows[i]["reading"]) for i in months if i in rows and rows[i]["reading"] is not None]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot([p[0] for p in pts], [p[1] for p in pts], ".", color="#1f77b4", label="NOAA global CFC-11")
    xs = [xval(i) for i in months]
    ax.plot(xs, [line_at(f, x) for x in xs], "-", color="#555555",
            label="Jan 2002 to Dec 2012 line, carried forward")
    fl = [r["month"] for r in q2 if r["flag"]]
    fi = [idx(int(m[:4]), int(m[5:])) for m in fl]
    ax.plot([xval(i) for i in fi], [rows[i]["reading"] for i in fi], "o", color="#d62728",
            markerfacecolor="none", markersize=9, label="flagged month")
    ax.set_xlabel("year")
    ax.set_ylabel("CFC-11 (ppt)")
    ax.set_title("Global CFC-11 against the 2002 to 2012 trend")
    ax.legend(loc="upper right")
    ax.text(0.01, 0.01, f"Data: {DOI}", transform=ax.transAxes, fontsize=8, va="bottom")
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("file", help="path to NOAA's HATS_global_F11.txt")
    ap.add_argument("--out", default=str(ROOT / "cases" / "C02"))
    args = ap.parse_args()
    run(args.file, args.out)


if __name__ == "__main__":
    main()
