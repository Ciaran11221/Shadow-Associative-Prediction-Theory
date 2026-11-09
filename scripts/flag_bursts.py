#!/usr/bin/env python3
"""Bursts (issue 28): does the flag count burst where the world was changing?

Flags and sources come from clean_gases.run, so they follow the same rules as every earlier run.
A gas year counts if it has 12 or more tested source months. It is judged if the gas has at least 2
earlier counting years. Its usual rate looks only at earlier counting years, never at that year or
a later one. A burst is a judged year whose Poisson chance is under 0.05 / N, N being the number of
gas years judged across all 16 gases.

Usage:
  python scripts/flag_bursts.py <noaa folder> <agage folder> --out <folder>
      [--seen <checks.csv> ...] [--seen-cfc11 <noaa folder> <agage folder>]

Writes the five files of clean_gases.py, plus bursts.csv, questions.csv and library/ (one JSON file per burst).
Seen bursts (from earlier runs) go in library/ marked "seen" and count in nothing.
Standard library, matplotlib and scipy.io.netcdf_file only.
"""
import argparse
import csv
import json
import math
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import c02_cfc11 as c  # noqa: E402
import clean_gases as g  # noqa: E402
import flag_ladder as fl  # noqa: E402

# name, NOAA file, kind of NOAA file, AGAGE gas code
BURST_GASES = [
    ("CFC-113", "HATS_global_F113.txt", "table:F113", "cfc-113"),
    ("HCFC-22", "HCFC22_GCMS_flask.txt", "gcms", "hcfc-22"),
    ("HCFC-142b", "HCFC142B_GCMS_flask.txt", "gcms", "hcfc-142b"),
    ("HFC-134a", "hfc134a_GCMS_flask.txt", "gcms", "hfc-134a"),
    ("HFC-152a", "hf152a_GCMS_flask.txt", "gcms", "hfc-152a"),
    ("HFC-32", "HFC-32_M2_PR1_MS_flask.txt", "m2pr1", "hfc-32"),
    ("HFC-125", "HFC-125_M2_PR1_MS_flask.txt", "m2pr1", "hfc-125"),
    ("HFC-143a", "HFC-143a_M2_PR1_MS_flask.txt", "m2pr1", "hfc-143a"),
    ("HFC-227ea", "HFC-227ea_GCMS_flask.txt", "gcms", "hfc-227ea"),
    ("HFC-365mfc", "HFC-365mfc_GCMS_flask.txt", "gcms", "hfc-365mfc"),
    ("SF6", "GML_global_SF6.txt", "table:GML:SF6", "sf6"),
    ("Nitrous oxide", "GML_global_N2O.txt", "table:GML:N2O", "n2o"),
    ("Methyl bromide", "CH3BR_GCMS_flask.txt", "gcms", "ch3br"),
    ("Methyl chloride", "CH3Cl_GCMS_flask.txt", "gcms", "ch3cl"),
    ("Perchloroethylene", "pce_GCMS_flask.txt", "gcms", "ccl2ccl2"),
    ("Dichloromethane", "ch2cl2_GCMS_flask.txt", "gcms", "ch2cl2"),
]

# The 13 gases with a NOAA flask file: all but CFC-113, SF6 and nitrous oxide.
FLASK_13 = [row[0] for row in BURST_GASES if row[0] not in ("CFC-113", "SF6", "Nitrous oxide")]

# kind, gases, from, to (month to month, ends inclusive)
STRETCHES = [
    ("up", ["HCFC-22", "HCFC-142b"], "2004-01", "2009-01"),
    ("up", ["HCFC-22"], "2005-01", "2012-06"),
    ("up", ["HFC-32", "HFC-125"], "2011-01", "2016-11"),
    ("up", ["HFC-134a", "HFC-143a", "HFC-32", "HFC-125", "HFC-152a"], "2016-01", "2023-12"),
    ("up", ["SF6"], "2001-01", "2010-04"),
    ("up", ["SF6"], "2008-01", "2020-02"),
    ("up", ["Dichloromethane"], "1998-01", "2014-07"),
    ("up", ["Dichloromethane"], "2011-01", "2021-11"),
    ("down", ["HFC-152a"], "2007-01", "2015-07"),
    ("down", ["HCFC-22"], "2011-01", "2016-11"),
    ("instrument", FLASK_13, "2008-07", "2009-06"),
    ("instrument", ["SF6"], "2021-01", "2022-12"),
    ("instrument", ["CFC-113"], "2023-10", "2024-12"),
]

MIN_MONTHS = 12        # tested source months for a gas year to count
MIN_EARLIER = 2        # earlier counting years for a gas year to be judged
RATE_FLOOR = 0.00182   # the usual rate is never below this
ALPHA = 0.05
SHUFFLES = 10000
SEEDS = {"q1": 28001, "q2": 28002, "down": 28003}  # fixed, one per question
STATION_BUILDS = ("one station, many gases", "one station, one gas")

BURST_COLUMNS = ["gas", "year", "tested", "flags", "judged", "usual_rate", "expected", "chance", "burst",
                 "inside", "outside", "down_only", "no_stretch", "build"]


def month_of(text):
    return c.idx(int(text[:4]), int(text[5:7]))


def poisson_tail(k, expected):
    """P(X >= k) for X Poisson with mean `expected`. Summed upward from k, never as 1 minus a lower sum."""
    if k <= 0:
        return 1.0
    if expected <= 0:
        return 0.0
    term = math.exp(-expected + k * math.log(expected) - math.lgamma(k + 1))
    total, j = term, k
    while True:
        j += 1
        term *= expected / j
        total += term
        if j > expected and term <= total * 1e-17:
            return min(total, 1.0)


# ---- stretches -------------------------------------------------------------------------------------------

def stretches_touched(gas, year, stretches=None):
    """The stretches (as list entries) that apply to `gas` and share any month with calendar `year`."""
    first, last = c.idx(year, 1), c.idx(year, 12)
    return [s for s in (STRETCHES if stretches is None else stretches)
            if gas in s[1] and month_of(s[2]) <= last and first <= month_of(s[3])]


def stretch_flags(gas, year, stretches=None):
    kinds = {s[0] for s in stretches_touched(gas, year, stretches)}
    inside = bool(kinds & {"up", "instrument"})
    return {"inside": inside, "touches_up": "up" in kinds,
            "down_only": "down" in kinds and not inside, "no_stretch": not kinds}


# ---- gas years -------------------------------------------------------------------------------------------

def gas_years(sources):
    """-> list of dicts, one per calendar year that counts (12 or more tested source months), in year order.
    Each has year, tested, flags, judged, usual_rate, expected, chance (None if not judged)."""
    tested, flags = {}, {}
    for s in sources:
        for m in s.tested:
            y = c.ym(m)[0]
            tested[y] = tested.get(y, 0) + 1
        for m in s.flags:
            y = c.ym(m)[0]
            flags[y] = flags.get(y, 0) + 1
    out, earlier_tested, earlier_flags, earlier_n = [], 0, 0, 0
    for y in sorted(tested):
        if tested[y] < MIN_MONTHS:
            continue
        row = {"year": y, "tested": tested[y], "flags": flags.get(y, 0), "judged": earlier_n >= MIN_EARLIER,
               "usual_rate": None, "expected": None, "chance": None}
        if row["judged"]:
            row["usual_rate"] = max(earlier_flags / earlier_tested, RATE_FLOOR)
            row["expected"] = row["tested"] * row["usual_rate"]
            row["chance"] = poisson_tail(row["flags"], row["expected"])
        out.append(row)
        earlier_tested += row["tested"]
        earlier_flags += row["flags"]
        earlier_n += 1
    return out


def mark_bursts(years_by_gas):
    """years_by_gas: {gas: gas_years rows}. Sets row['burst'] and returns (N judged, bar = 0.05 / N)."""
    n = sum(r["judged"] for rows in years_by_gas.values() for r in rows)
    bar = ALPHA / n if n else None
    for rows in years_by_gas.values():
        for r in rows:
            r["burst"] = bool(r["judged"] and r["chance"] < bar)
    return n, bar


# ---- builds ----------------------------------------------------------------------------------------------

def flagged_months(sources, year):
    """{source id: sorted months} for the flags of these sources inside calendar `year`."""
    out = {}
    for s in sources:
        months = sorted(m for m in s.flags if c.ym(m)[0] == year)
        if months:
            out[s.id] = months
    return out


def other_gases_at(source_id, months, gas, sources_by_gas):
    """The other gases whose same source flagged in any of `months`."""
    wanted = set(months)
    return [name for name, srcs in sources_by_gas.items() if name != gas
            and any(s.id == source_id and s.flags & wanted for s in srcs)]


def build_of(gas, year, sources_by_gas):
    """-> (build, details). Builds: air, one station, many gases / one gas, unsorted."""
    sources = sources_by_gas[gas]
    flagged = flagged_months(sources, year)
    total = sum(len(v) for v in flagged.values())
    if not total:
        return "unsorted", {"top_share": None}
    top = max(len(v) for v in flagged.values())
    top_share = top / total
    by_id = {s.id: s for s in sources}
    labs = {by_id[i].lab for i in flagged}
    if len(flagged) >= 3 and labs >= set(fl.LABS) and top_share < 0.5:
        return "air", {"top_share": top_share}
    leaders = [i for i, v in flagged.items() if len(v) == top]
    if top_share >= 0.5 and len(leaders) == 1:
        others = other_gases_at(leaders[0], flagged[leaders[0]], gas, sources_by_gas)
        if len(others) >= 2:
            return "one station, many gases", {"top_share": top_share, "station": leaders[0]}
        if not others:
            return "one station, one gas", {"top_share": top_share, "station": leaders[0]}
    return "unsorted", {"top_share": top_share}


# ---- questions -------------------------------------------------------------------------------------------

def rate(a, b):
    return a / b if b else None


def ratio_text(r):
    return "n/a" if r is None else "inf" if r == math.inf else f"{r:.3f}"


def question_1(rows_by_gas, shuffles=SHUFFLES, seed=SEEDS["q1"]):
    """rows_by_gas: {gas: gas_years rows with burst and stretch flags}. -> dict of every number."""
    eligible = []
    for gas, rows in rows_by_gas.items():
        judged = [r for r in rows if r["judged"]]
        if sum(r["inside"] for r in judged) >= 2 and sum(not r["inside"] for r in judged) >= 2:
            eligible.append((gas, judged))
    inside_years = sum(r["inside"] for _, js in eligible for r in js)
    outside_years = sum(not r["inside"] for _, js in eligible for r in js)
    in_b = sum(r["burst"] for _, js in eligible for r in js if r["inside"])
    out_b = sum(r["burst"] for _, js in eligible for r in js if not r["inside"])
    out = {"eligible_gases": len(eligible), "inside_years": inside_years, "outside_years": outside_years,
           "bursts_inside": in_b, "bursts_outside": out_b, "shuffles": shuffles, "seed": seed,
           "rate_inside": rate(in_b, inside_years), "rate_outside": rate(out_b, outside_years)}
    if not eligible:
        out.update({"ratio": None, "chance": None, "verdict": "not judged"})
        return out
    rng = random.Random(seed)
    counts = [(sum(r["burst"] for r in js), [r["inside"] for r in js]) for _, js in eligible]
    hits = 0
    for _ in range(shuffles):
        got = sum(sum(rng.sample(flags, b)) for b, flags in counts)
        hits += got >= in_b
    chance = (1 + hits) / (1 + shuffles)
    ri, ro = out["rate_inside"], out["rate_outside"]
    out["ratio"] = (math.inf if in_b else None) if not ro else ri / ro
    big_enough = in_b > 0 if not ro else ri >= 2 * ro
    out["chance"] = chance
    out["verdict"] = "pass" if chance < 0.05 and big_enough else "fail"
    return out


def question_2(bursts, shuffles=SHUFFLES, seed=SEEDS["q2"]):
    """bursts: list of dicts with gas, build, touches_up. Up stretches only."""
    air = [b for b in bursts if b["build"] == "air"]
    station = [b for b in bursts if b["build"] in STATION_BUILDS]
    air_in, st_in = sum(b["touches_up"] for b in air), sum(b["touches_up"] for b in station)
    a_share, s_share = rate(air_in, len(air)), rate(st_in, len(station))
    out = {"air_bursts": len(air), "air_inside_up": air_in, "station_bursts": len(station),
           "station_inside_up": st_in, "air_share": a_share, "station_share": s_share,
           "shuffles": shuffles, "seed": seed, "ratio": None, "chance": None}
    if len(air) < 5 or len(station) < 5:
        out["verdict"] = "void"
        return out
    out["ratio"] = (math.inf if air_in else None) if not s_share else a_share / s_share
    observed = a_share - s_share
    groups = {}
    for b in bursts:
        groups.setdefault(b["gas"], []).append(b)
    layout = [([b["build"] for b in bs], [b["touches_up"] for b in bs]) for bs in groups.values()]
    rng = random.Random(seed)
    hits = 0
    for _ in range(shuffles):
        ai = si = 0
        for builds, ups in layout:
            order = builds[:]
            rng.shuffle(order)
            for build, up in zip(order, ups):
                if up:
                    ai += build == "air"
                    si += build in STATION_BUILDS
        hits += (ai / len(air) - si / len(station)) >= observed - 1e-12
    chance = (1 + hits) / (1 + shuffles)
    out["chance"] = chance
    big_enough = air_in > 0 if not s_share else a_share >= 2 * s_share
    out["verdict"] = "pass" if chance < 0.05 and big_enough else "fail"
    return out


def down_check(rows_by_gas, shuffles=SHUFFLES, seed=SEEDS["down"]):
    """The down check. rows_by_gas: {gas: gas_years rows with burst and stretch flags}."""
    down_years = sum(r["down_only"] for rows in rows_by_gas.values() for r in rows if r["judged"])
    none_years = sum(r["no_stretch"] for rows in rows_by_gas.values() for r in rows if r["judged"])
    down_b = sum(r["burst"] for rows in rows_by_gas.values() for r in rows if r["judged"] and r["down_only"])
    none_b = sum(r["burst"] for rows in rows_by_gas.values() for r in rows if r["judged"] and r["no_stretch"])
    out = {"down_only_years": down_years, "down_only_bursts": down_b, "no_stretch_years": none_years,
           "no_stretch_bursts": none_b, "shuffles": shuffles, "seed": seed,
           "rate_down_only": rate(down_b, down_years), "rate_no_stretch": rate(none_b, none_years), "chance": None}
    if down_years < 10:
        out["verdict"] = "not judged"
        return out
    layout = []
    for rows in rows_by_gas.values():
        pool = [r for r in rows if r["judged"] and (r["down_only"] or r["no_stretch"])]
        if pool:
            layout.append((sum(r["burst"] for r in pool), [r["down_only"] for r in pool]))
    rng = random.Random(seed)
    hits = 0
    for _ in range(shuffles):
        hits += sum(sum(rng.sample(flags, b)) for b, flags in layout) >= down_b
    chance = (1 + hits) / (1 + shuffles)
    out["chance"] = chance
    rd, rn = out["rate_down_only"], out["rate_no_stretch"]
    above = rd > (rn or 0)
    out["verdict"] = "check the rule or the list" if chance < 0.05 and above else "ok"
    return out


# ---- a run on a set of sources ---------------------------------------------------------------------------

def analyse(sources_by_gas, stretches=None):
    """sources_by_gas: {gas: [ladder sources]}. -> dict with rows_by_gas, bursts (list), n, bar.
    stretches: the list to use (None means STRETCHES); a seen run passes [] since no stretch applies to it."""
    rows_by_gas = {gas: gas_years(srcs) for gas, srcs in sources_by_gas.items()}
    n, bar = mark_bursts(rows_by_gas)
    bursts = []
    for gas, rows in rows_by_gas.items():
        for r in rows:
            r.update(stretch_flags(gas, r["year"], stretches) if r["judged"] else
                     {"inside": None, "touches_up": None, "down_only": None, "no_stretch": None})
            r["build"] = None
            if r["burst"]:
                r["build"], r["details"] = build_of(gas, r["year"], sources_by_gas)
                bursts.append({"gas": gas, **r})
    return {"rows_by_gas": rows_by_gas, "bursts": bursts, "n": n, "bar": bar}


def library_entry(burst, sources_by_gas, stretches, seen=False):
    gas, year = burst["gas"], burst["year"]
    sources = sources_by_gas[gas]
    flagged = flagged_months(sources, year)
    by_id = {s.id: s for s in sources}
    listed = []
    for sid, months in flagged.items():
        s = by_id[sid]
        listed.append({"source": sid, "lab": s.lab, "south": s.south,
                       "months": [c.label(m) for m in months],
                       "other_gases_flagged": other_gases_at(sid, months, gas, sources_by_gas)})
    north = [m for sid, ms in flagged.items() if not by_id[sid].south for m in ms]
    south = [m for sid, ms in flagged.items() if by_id[sid].south for m in ms]
    touched = stretches_touched(gas, year, stretches)
    entry = {"gas": gas, "year": year, "tested": burst["tested"], "flags": burst["flags"],
             "expected": burst["expected"], "chance": burst["chance"], "sources": listed,
             "labs": sorted({s["lab"] for s in listed}),
             "first_flag_north": c.label(min(north)) if north else None,
             "first_flag_south": c.label(min(south)) if south else None,
             "build": burst["build"], "top_share": burst["details"]["top_share"],
             "stretches": [f"{k} {f} to {t}" for k, _, f, t in touched]}
    if seen:
        entry["seen"] = True
    return entry


# ---- seen runs -------------------------------------------------------------------------------------------

def sources_from_checks(path):
    """A checks.csv from an earlier run -> {gas: [ladder sources]}."""
    tested, flags, order = {}, {}, {}
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            key = (row["gas"], row["source"])
            order.setdefault(row["gas"], [])
            if key not in tested:
                tested[key], flags[key] = set(), set()
                order[row["gas"]].append(row["source"])
            if row["skipped"] != "true":
                tested[key].add(g.month_index(row["month"]))
                if row["flag"] == "true":
                    flags[key].add(g.month_index(row["month"]))
    out = {}
    for gas, ids in order.items():
        out[gas] = []
        for sid in ids:
            lab, _, code = sid.partition(" ")
            out[gas].append(fl.make_source(lab, code, flags[(gas, sid)], tested[(gas, sid)]))
    return out


def seen_runs(seen_files, cfc11):
    """-> list of (label, {gas: sources}). cfc11: None or (noaa folder, agage folder)."""
    runs = [(Path(p).parent.name or Path(p).stem, sources_from_checks(p)) for p in seen_files]
    if cfc11:
        res = g.run_gas("CFC-11", cfc11[0], cfc11[1], "HATS_global_F11.txt", "table:F11", "cfc-11")
        runs.append(("CFC-11", {"CFC-11": res["sources"]}))
    return runs


# ---- output ----------------------------------------------------------------------------------------------

def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def tf(v):
    return "" if v is None else str(bool(v)).lower()


def bursts_rows(rows_by_gas):
    out = []
    for gas, rows in rows_by_gas.items():
        for r in rows:
            out.append([gas, r["year"], r["tested"], r["flags"], tf(r["judged"]), g.cell(r["usual_rate"]),
                        g.cell(r["expected"]), g.cell(r["chance"]), tf(r["burst"]) if r["judged"] else "",
                        tf(r["inside"]), tf(None if r["inside"] is None else not r["inside"]),
                        tf(r["down_only"]), tf(r["no_stretch"]), r["build"] or ""])
    return out


def question_rows(n, bar, total_bursts, q1, q2, dc):
    rows = [["bursts", "gas_years_judged", n], ["bursts", "bar", g.cell(bar)], ["bursts", "bursts", total_bursts]]
    for name, q in (("question 1", q1), ("question 2", q2), ("down check", dc)):
        for k, v in q.items():
            rows.append([name, k, g.cell(v) if not isinstance(v, float) or math.isfinite(v) else "inf"])
    return rows


def closing_lines(n, bar, total, q1, q2, dc):
    f = lambda v: "n/a" if v is None else f"{v:.4f}"  # noqa: E731
    return [
        f"bursts {total} in {n} gas years judged, bar {'n/a' if bar is None else f'{bar:.3g}'}",
        f"question 1: inside {q1['bursts_inside']} bursts in {q1['inside_years']} years, outside "
        f"{q1['bursts_outside']} in {q1['outside_years']}, ratio {ratio_text(q1['ratio'])}, chance {f(q1['chance'])}, "
        f"{q1['verdict']}",
        f"question 2: air {q2['air_inside_up']} of {q2['air_bursts']} inside up stretches, one station "
        f"{q2['station_inside_up']} of {q2['station_bursts']}, ratio {ratio_text(q2['ratio'])}, chance {f(q2['chance'])}, "
        f"{q2['verdict']}",
        f"down check: down only {dc['down_only_bursts']} bursts in {dc['down_only_years']} years, no stretch "
        f"{dc['no_stretch_bursts']} in {dc['no_stretch_years']}, chance {f(dc['chance'])}, {dc['verdict']}",
    ]


def run(noaa_folder, agage_folder, out, gases=BURST_GASES, seen_files=(), cfc11=None):
    out = Path(out)
    results = g.run(noaa_folder, agage_folder, out, gases)["gases"]
    sources_by_gas = {r["gas"]: r["sources"] for r in results}
    main = analyse(sources_by_gas)
    q1 = question_1(main["rows_by_gas"])
    q2 = question_2(main["bursts"])
    dc = down_check(main["rows_by_gas"])

    g.write_csv(out / "bursts.csv", BURST_COLUMNS, bursts_rows(main["rows_by_gas"]))
    g.write_csv(out / "questions.csv", ["question", "item", "value"],
                question_rows(main["n"], main["bar"], len(main["bursts"]), q1, q2, dc))
    library = out / "library"
    library.mkdir(exist_ok=True)
    for old in library.glob("*.json"):
        old.unlink()
    for b in main["bursts"]:
        entry = library_entry(b, sources_by_gas, None)
        (library / f"{slug(b['gas'])}-{b['year']}.json").write_text(json.dumps(entry, indent=2) + "\n", encoding="utf-8")
    seen_count = 0
    for k, (label, run_sources) in enumerate(seen_runs(seen_files, cfc11), 1):
        sub = analyse(run_sources, stretches=[])
        for b in sub["bursts"]:
            entry = library_entry(b, run_sources, [], seen=True)
            name = f"seen{k}-{slug(b['gas'])}-{b['year']}.json"
            (library / name).write_text(json.dumps(entry, indent=2) + "\n", encoding="utf-8")
            seen_count += 1
    print(f"seen bursts written to the library: {seen_count}")
    for line in closing_lines(main["n"], main["bar"], len(main["bursts"]), q1, q2, dc):
        print(line)
    return {"main": main, "q1": q1, "q2": q2, "down": dc}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("noaa", help="folder holding NOAA's files for the 16 gases")
    ap.add_argument("agage", help="folder holding the AGAGE .nc files for the 16 gases")
    ap.add_argument("--out", required=True, help="folder to write the CSV files and library to")
    ap.add_argument("--seen", nargs="+", action="append", default=[], metavar="CHECKS_CSV",
                    help="checks.csv files from earlier runs; their bursts go in library/ marked seen")
    ap.add_argument("--seen-cfc11", nargs=2, metavar=("NOAA", "AGAGE"),
                    help="run CFC-11 from these two folders and add its bursts as seen")
    args = ap.parse_args()
    run(args.noaa, args.agage, args.out, seen_files=[p for group in args.seen for p in group], cfc11=args.seen_cfc11)


if __name__ == "__main__":
    main()
