#!/usr/bin/env python3
"""Clean gas run (issues 21 and 23): the C02 rule and the flag ladder on four gases with no scandal.

Gases: H-1211, H-1301, H-2402 and methyl chloroform. Each has NOAA flask data and AGAGE NetCDF files.

Usage:
  python scripts/clean_gases.py <noaa folder> <agage folder> --out <folder>

Writes checks.csv, sources.csv, months.csv, by_year.csv and summary.csv to --out.
Every flag comes from c02_cfc11.roll(reading, i, min_share=GAP_SHARE); Gosan from c02_agage.gosan_record.
A month with no sample has no reading: nothing is filled, interpolated or averaged across a gap.
Standard library, matplotlib and scipy.io.netcdf_file only.
"""
import argparse
import csv
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import c02_agage as a  # noqa: E402
import c02_cfc11 as c  # noqa: E402
import flag_ladder as fl  # noqa: E402

# name, NOAA file, kind of NOAA file, AGAGE gas code
GASES = [
    ("H-1211", "HAL1211_GCMS_flask.txt", "gcms", "h-1211"),
    ("H-1301", "H-1301_M2_PR1_MS_flask.txt", "h1301", "h-1301"),
    ("H-2402", "Hal2402_GCMS_flask.txt", "gcms", "h-2402"),
    ("methyl chloroform", "HATS_global_MC.txt", "table", "ch3ccl3"),
]
SAME_STATION = {"mlo_pfp": "mlo"}
NOT_STATIONS = {"NH", "SH", "Global"}
TABLE_COLUMN = re.compile(r"^HATS_(.+)_MC$")


def fail(message):
    sys.exit(f"error: {message}")


def site_code(text):
    code = text.strip().lower()
    return SAME_STATION.get(code, code)


def number(text, where):
    """A finite number, or a stop with an error."""
    try:
        v = float(text)
    except ValueError:
        fail(f"{where}: mole fraction {text!r} is not a number")
    if not math.isfinite(v):
        fail(f"{where}: mole fraction {text!r} is not a number")
    return v


def month_from_yyyymmdd(text, where):
    text = text.strip()
    if len(text) != 8 or not text.isdigit():
        fail(f"{where}: date {text!r} is not yyyymmdd")
    return c.idx(int(text[:4]), int(text[4:6]))


def lines_of(path):
    return Path(path).read_bytes().decode("utf-8", errors="replace").replace("\r\n", "\n").split("\n")


def monthly_average(samples):
    """samples: {site: {month index: [values]}} -> {site: {month index: plain average}}."""
    return {site: {i: math.fsum(v) / len(v) for i, v in months.items()} for site, months in samples.items()}


def read_gcms(path):
    """Tab separated: a note line, a column line, then rows. -> {site: {month: average}}."""
    samples, header = {}, False
    for n, text in enumerate(lines_of(path), 1):
        if n == 1 or not text.strip():
            continue
        parts = [p.strip() for p in text.split("\t")]
        if not header:
            if parts[0].lower() != "site" or len(parts) != 7:
                fail(f"{path} line {n}: expected the column line (7 tab separated fields starting with site)")
            header = True
            continue
        if len(parts) != 7:
            fail(f"{path} line {n}: expected 7 tab separated fields, found {len(parts)}")
        where = f"{Path(path).name} line {n}"
        month = month_from_yyyymmdd(parts[2].split()[0] if parts[2].split() else "", where)
        value = number(parts[5], where)
        samples.setdefault(site_code(parts[0]), {}).setdefault(month, []).append(value)
    if not header:
        fail(f"{path}: no column line found")
    return monthly_average(samples)


def read_h1301(path):
    """26 comment lines, a column line, rows. Same site, date and time from M2 and PR1 is one sample: keep PR1."""
    rows, header = [], False
    for n, text in enumerate(lines_of(path), 1):
        if text.startswith("#") or not text.strip():
            continue
        parts = text.split()
        if not header:
            if parts[0].lower() != "site" or len(parts) != 10:
                fail(f"{path} line {n}: expected the column line (10 fields starting with site)")
            header = True
            continue
        if len(parts) != 10:
            fail(f"{path} line {n}: expected 10 fields, found {len(parts)}")
        where = f"{Path(path).name} line {n}"
        if parts[8] != "-":
            fail(f"{where}: flag {parts[8]!r} is not '-'; no rule exists for it")
        rows.append((site_code(parts[0]), parts[2], parts[3], parts[9],
                     month_from_yyyymmdd(parts[2], where), number(parts[6], where)))
    if not header:
        fail(f"{path}: no column line found")
    pr1 = {(site, day, hhmm) for site, day, hhmm, instr, _, _ in rows if instr == "PR1"}
    samples = {}
    for site, day, hhmm, instr, month, value in rows:
        if instr == "M2" and (site, day, hhmm) in pr1:
            continue
        samples.setdefault(site, {}).setdefault(month, []).append(value)
    return monthly_average(samples)


def read_table(path):
    """Combined table: comment lines, a column line, rows. Station columns only; nan is no reading."""
    names, cols = None, {}
    for n, text in enumerate(lines_of(path), 1):
        if text.startswith("#") or not text.strip():
            continue
        parts = text.split()
        if names is None:
            names = parts
            for need in ("HATS_MC_YYYY", "HATS_MC_MM"):
                if need not in names:
                    fail(f"{path}: column {need} not found")
            cols = {}
            for k, name in enumerate(names):
                m = TABLE_COLUMN.match(name)
                if m and m.group(1) not in NOT_STATIONS:
                    cols[k] = (site_code(m.group(1)), {})
            continue
        if len(parts) != len(names):
            fail(f"{path} line {n}: expected {len(names)} fields, found {len(parts)}")
        i = c.idx(int(parts[names.index("HATS_MC_YYYY")]), int(parts[names.index("HATS_MC_MM")]))
        for k, (_, data) in cols.items():
            if i in data:
                continue
            data[i] = None if parts[k].lower() == "nan" else number(parts[k], f"{Path(path).name} line {n}")
    if names is None:
        fail(f"{path}: no column line found")
    return {site: {i: v for i, v in data.items() if v is not None} for site, data in cols.values()}


def month_index(label):
    return c.idx(int(label[:4]), int(label[5:]))


def source_of(lab, code, reading, recs):
    """Build the ladder source and the check rows from a list of roll records."""
    tested = {month_index(r["month"]) for r in recs if not r["skipped"]}
    flags = {month_index(r["month"]) for r in recs if r["flag"]}
    return fl.make_source(lab, code, flags, tested), recs, reading


def run_one(lab, code, data):
    """The 10 year rule on one source. data: {month index: value}."""
    present = [i for i, v in data.items() if v is not None]
    last = max(present) if present else None
    if last is None or last < c.idx(2005, 1):
        recs = []
    else:
        recs = [c.roll(data.get, i, min_share=a.GAP_SHARE) for i in range(c.idx(2005, 1), last + 1)]
    return source_of(lab, code, data.get, recs)


def find_file(folder, name):
    hits = [p for p in Path(folder).iterdir() if p.name.lower() == name.lower()]
    if not hits:
        fail(f"no file named {name} in {folder}")
    return hits[0]


def agage_stations(folder, gas):
    pattern = re.compile(rf"^agage_([a-z0-9]+)_{re.escape(gas)}_monthly-baseline-.+\.nc$", re.I)
    found = {}
    for p in sorted(Path(folder).iterdir()):
        m = pattern.match(p.name)
        if m:
            found[m.group(1).lower()] = p
    return found


def noaa_data(folder, filename, kind):
    path = find_file(folder, filename)
    return {"gcms": read_gcms, "h1301": read_h1301, "table": read_table}[kind](path)


def run_gas(name, noaa_folder, agage_folder, filename, kind, gas):
    """-> dict with sources (ladder sources), checks (rows), months (ladder), gosan (summary bits)."""
    entries = []  # (source, recs, reading function)
    for code, data in sorted(noaa_data(noaa_folder, filename, kind).items()):
        entries.append(run_one("NOAA", code, data))
    stations = agage_stations(agage_folder, gas)
    if not stations:
        fail(f"no AGAGE files for {gas} in {agage_folder}")
    gosan = None
    for code, path in stations.items():
        data = a.read_monthly(path)
        if code == "gsn":
            hf = [p for p in Path(agage_folder).iterdir()
                  if re.match(rf"^agage_gsn_{re.escape(gas)}_[0-9]+\.nc$", p.name, re.I)]
            if not hf:
                fail(f"no Gosan high frequency file for {gas} in {agage_folder}")
            means = a.read_monthly_means(hf[0])
            excess = a.excess_of(means, data)
            _, recs = a.gosan_record(means, data, a.GAP_SHARE)
            gosan = source_of("AGAGE", "gsn", excess.get, recs)
            entries.append(gosan)
        else:
            entries.append(run_one("AGAGE", code, data))
    sources = [e[0] for e in entries]
    tested_all = [m for s in sources for m in s.tested]
    last = max(tested_all) if tested_all else c.idx(2005, 1) - 1
    months = fl.ladder(sources, c.idx(2005, 1), last) if tested_all else []
    return {"gas": name, "entries": entries, "sources": sources, "months": months,
            "months18": fl.ladder([s for s in sources if s.in_cfc11_set], c.idx(2005, 1), last) if tested_all else [],
            "gosan": gosan[0] if gosan else None}


def cell(v):
    return "" if v is None else repr(v) if isinstance(v, float) else v


def write_csv(path, header, rows):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


def summary_row(g):
    sources, months, m18 = g["sources"], g["months"], g["months18"]
    out = {"gas": g["gas"], "sources_listed": len(sources), "sources_tested": sum(bool(s.tested) for s in sources)}
    for tag, pick in (("", sources), ("_noaa", [s for s in sources if s.lab == "NOAA"]),
                      ("_agage", [s for s in sources if s.lab == "AGAGE"])):
        t, f = sum(len(s.tested) for s in pick), sum(len(s.flags) for s in pick)
        out[f"tested{tag}"], out[f"flags{tag}"] = t, f
        out[f"flag_rate{tag}"] = f / t if t else None
    possible = sum(m["possible"] for m in months)
    out.update({"months_run": len(months), "months_possible": possible, "gas_years": possible / 12})
    for lv in range(5):
        out[f"months_level_{lv}"] = sum(m["level"] == lv for m in months)
    l3 = sum(m["level"] >= 3 for m in months)
    out.update({"months_level_3plus": l3, "share_3plus_of_possible": l3 / possible if possible else None,
                "top_level": max((m["level"] for m in months), default=0)})
    for lv in range(1, 5):
        first = fl.first_at(months, lv)
        out[f"first_level_{lv}"] = c.label(first["month"]) if first else None
    runs = fl.runs([m["level"] for m in months])
    out.update({"level_3_runs": runs, "runs_per_gas_year": runs / out["gas_years"] if out["gas_years"] else None,
                "top_level_18": max((m["level_18"] for m in m18), default=0) if m18 else 0,
                "months_level_3plus_18": sum(m["level_18"] >= 3 for m in m18),
                "months_one_lab_3plus": sum(m["one_lab_3plus"] for m in months)})
    gs = g["gosan"]
    out.update({"gosan_tested": len(gs.tested) if gs else None, "gosan_flags": len(gs.flags) if gs else None,
                "gosan_first_flag": c.label(min(gs.flags)) if gs and gs.flags else None})
    return out


def run(noaa_folder, agage_folder, out, gases=GASES):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    results = [run_gas(name, noaa_folder, agage_folder, fn, kind, gas) for name, fn, kind, gas in gases]
    checks, srcs, mons, years, summaries = [], [], [], [], []
    for g in results:
        for s, recs, reading in g["entries"]:
            for r in recs:
                i = month_index(r["month"])
                mult = c.multiple_of(r) if r["usual_miss"] is not None else None
                checks.append([g["gas"], s.id, r["month"], cell(reading(i)), cell(r["line_value"]), cell(r["usual_miss"]),
                               cell(r["gap"]), cell(r["threshold"]), cell(mult), "skipped" if r["skipped"] else str(r["flag"]).lower(),
                               str(r["skipped"]).lower(), r["skip_reason"] or ""])
            flags = sorted(s.flags)
            srcs.append([g["gas"], s.id, s.lab, str(s.south).lower(), str(s.in_cfc11_set).lower(), len(s.tested),
                         len(recs) - len(s.tested), len(s.flags), c.label(flags[0]) if flags else "",
                         c.label(flags[-1]) if flags else ""])
        m18 = {m["month"]: m for m in g["months18"]}
        for m in g["months"]:
            mons.append([g["gas"], c.label(m["month"]), str(m["possible"]).lower(), m["level"], m["count"],
                         ";".join(m["labs"]), ";".join(m["sources"]), m18[m["month"]]["level_18"],
                         m18[m["month"]]["count_18"], str(m["one_lab_3plus"]).lower()])
        for y in sorted({c.ym(m["month"])[0] for m in g["months"]}):
            ms = [m for m in g["months"] if c.ym(m["month"])[0] == y]
            years.append([g["gas"], y, sum(m["possible"] for m in ms)] + [sum(m["level"] == lv for m in ms) for lv in range(5)])
        summaries.append(summary_row(g))
    write_csv(out / "checks.csv", ["gas", "source", "month", "reading", "line_value", "usual_miss", "gap", "threshold",
                                   "multiple", "flag", "skipped", "skip_reason"], checks)
    write_csv(out / "sources.csv", ["gas", "source", "lab", "south", "in_cfc11_set", "tested", "skipped", "flags",
                                    "first_flag", "last_flag"], srcs)
    write_csv(out / "months.csv", ["gas", "month", "possible", "level", "count", "labs", "sources", "level_18",
                                   "count_18", "one_lab_3plus"], mons)
    write_csv(out / "by_year.csv", ["gas", "year", "possible", "level_0", "level_1", "level_2", "level_3", "level_4"], years)
    keys = list(summaries[0].keys())
    write_csv(out / "summary.csv", keys, [[cell(r[k]) for k in keys] for r in summaries])

    for r in summaries:
        print(f"{r['gas']}: sources {r['sources_listed']} ({r['sources_tested']} tested), source-months tested {r['tested']}, "
              f"flags {r['flags']}, months run {r['months_run']}, possible {r['months_possible']}, top level {r['top_level']}, "
              f"level 3 runs {r['level_3_runs']}")
    reach = [r["gas"] for r in summaries if r["top_level"] >= 3]
    reach18 = [r["gas"] for r in summaries if r["top_level_18"] >= 3]
    gosan = [r["gas"] for r in summaries if r["gosan_flags"]]
    print(f"gases reaching level 3: {len(reach)} of {len(summaries)}")
    print(f"gases reaching level 3 on the CFC-11 set: {len(reach18)} of {len(summaries)}")
    print(f"gosan flagged on: {', '.join(gosan) if gosan else 'none'}")
    return {"gases": results, "summary": summaries}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("noaa", help="folder holding NOAA's files for the four gases")
    ap.add_argument("agage", help="folder holding the AGAGE .nc files for the four gases")
    ap.add_argument("--out", required=True, help="folder to write the CSV files to")
    args = ap.parse_args()
    run(args.noaa, args.agage, args.out)


if __name__ == "__main__":
    main()
