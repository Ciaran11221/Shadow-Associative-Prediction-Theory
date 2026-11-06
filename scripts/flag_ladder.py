#!/usr/bin/env python3
"""The flag ladder (issue 21, rules on issue 23): how many separate sources flagged in the last 12 months?

A source is one lab's record at one station. Labs: NOAA, AGAGE. Levels stack:
  0  no source
  1  1 source
  2  2 or more sources, and not level 3 or 4
  3  3 or more sources from both labs, and not level 4
  4  10 or more sources from both labs, with at least one north and one south
The ladder takes sources that already carry their flags; it reads no files.

Benchmark (CFC-11, the case the ladder was first shaped on):
  python scripts/flag_ladder.py <HATS_global_F11.txt> <folder of CFC-11 AGAGE files>
Every flag comes from c02_cfc11.roll(reading, i, min_share=GAP_SHARE); Gosan from c02_agage.gosan_record.
Standard library only (the benchmark also needs scipy via c02_agage).
"""
import argparse
import sys
from collections import namedtuple
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import c02_agage as a  # noqa: E402
import c02_cfc11 as c  # noqa: E402

START = c.idx(2005, 1)
WINDOW = 12  # a flag counts in its own month and the 11 after it
LABS = ("NOAA", "AGAGE")
SOUTH = {"NOAA": {"spo", "psa", "cgo", "smo"}, "AGAGE": {"cgo", "smo"}}
CFC11_SET = {("NOAA", code) for code in "alt sum brw mhd thd nwr kum mlo smo cgo psa spo".split()} \
    | {("AGAGE", code) for code in "mhd thd rpb smo cgo gsn".split()}

Source = namedtuple("Source", "id lab code south in_cfc11_set flags tested")


def make_source(lab, code, flags, tested):
    """flags and tested: iterables of month index. A flag outside tested is a mistake."""
    flags, tested = frozenset(flags), frozenset(tested)
    if not flags <= tested:
        raise ValueError(f"{lab} {code}: flags outside tested months")
    return Source(f"{lab} {code}", lab, code, code in SOUTH[lab], (lab, code) in CFC11_SET, flags, tested)


def level_of(flagged):
    """flagged: sources with a flag in the window. Returns the level 0 to 4."""
    n = len(flagged)
    both = {s.lab for s in flagged} >= set(LABS)
    if n >= 10 and both and any(s.south for s in flagged) and any(not s.south for s in flagged):
        return 4
    if n >= 3 and both:
        return 3
    if n >= 2:
        return 2
    return n


def in_window(months, i):
    return any(m in months for m in range(i - WINDOW + 1, i + 1))


def is_possible(sources, i):
    """Level 3 is possible when 3 or more sources had a tested month in the window, and both labs are among them."""
    active = [s for s in sources if in_window(s.tested, i)]
    return len(active) >= 3 and {s.lab for s in active} >= set(LABS)


def ladder(sources, first, last):
    """One dict per month from first to last (month index)."""
    out = []
    for i in range(first, last + 1):
        flagged = [s for s in sources if in_window(s.flags, i)]
        in18 = [s for s in flagged if s.in_cfc11_set]
        per_lab = {lab: sum(s.lab == lab for s in flagged) for lab in LABS}
        out.append({"month": i, "possible": is_possible(sources, i), "level": level_of(flagged),
                    "count": len(flagged), "labs": sorted({s.lab for s in flagged}),
                    "sources": sorted(s.id for s in flagged),
                    "level_18": level_of(in18), "count_18": len(in18),
                    "one_lab_3plus": any(n >= 3 for n in per_lab.values())})
    return out


def runs(levels, minimum=3):
    """Number of runs of consecutive months at `minimum` or more."""
    n, inside = 0, False
    for lv in levels:
        if lv >= minimum and not inside:
            n += 1
        inside = lv >= minimum
    return n


def first_at(months, level, key="level", since=0):
    """The first month dict from month index `since` whose level is `level` or higher, or None."""
    return next((m for m in months if m["month"] >= since and m[key] >= level), None)


def benchmark(f11_path, agage_folder):
    comments, cols = c.read_file(f11_path)
    sources, noaa_tested, noaa_flags = [], 0, 0
    for name, data in cols.items():
        code = c.COLUMN.match(name).group(1)
        if code in ("NH", "SH", "Global"):
            continue
        reading = data.get
        have = [i for i, v in data.items() if v is not None]
        last = max(have) if have else -1
        recs = [c.roll(reading, i, min_share=a.GAP_SHARE) for i in range(START, last + 1)] if last >= START else []
        tested = {c.idx(int(r["month"][:4]), int(r["month"][5:])) for r in recs if not r["skipped"]}
        flags = {c.idx(int(r["month"][:4]), int(r["month"][5:])) for r in recs if r["flag"]}
        noaa_tested += len(tested)
        noaa_flags += len(flags)
        sources.append(make_source("NOAA", code.lower(), flags, tested))
    agage = []
    for code, name in a.LONG:
        path = a.find(agage_folder, f"agage_{code}_cfc-11_monthly-baseline-*.nc")
        agage.append((code, a.long_record(code, name, a.read_monthly(path), a.GAP_SHARE)[1]))
    baseline = a.read_monthly(a.find(agage_folder, "agage_gsn_cfc-11_monthly-baseline-*.nc"))
    means = a.read_monthly_means(a.find(agage_folder, "agage_gsn_cfc-11_[0-9]*.nc"))
    agage.append(("gsn", a.gosan_record(means, baseline, a.GAP_SHARE)[1]))
    for code, recs in agage:
        tested = {c.idx(int(r["month"][:4]), int(r["month"][5:])) for r in recs if not r["skipped"]}
        flags = {c.idx(int(r["month"][:4]), int(r["month"][5:])) for r in recs if r["flag"]}
        sources.append(make_source("AGAGE", code, flags, tested))
    last = max(m for s in sources for m in s.tested)
    months = ladder(sources, START, last)
    cfc = [s for s in sources if s.in_cfc11_set]
    months18 = ladder(cfc, START, last)
    before = [m for m in months18 if m["month"] < c.idx(2013, 1)]
    print(f"sources: {len(sources)} ({len(cfc)} in the CFC-11 set)")
    print(f"NOAA tested months: {noaa_tested}  flags: {noaa_flags}")
    print(f"months before 2013: {len(before)}")
    for lv in range(5):
        print(f"  level {lv}: {sum(m['level'] == lv for m in before)}")
    for since, text in ((0, "ever"), (c.idx(2013, 1), "from 2013")):
        for lv in range(1, 5):
            m = first_at(months18, lv, since=since)
            print(f"first month at level {lv} or higher, {text}: "
                  + (f"{c.label(m['month'])} with {m['count']} sources" if m else "none"))
    return months18


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("f11", help="path to NOAA's HATS_global_F11.txt")
    ap.add_argument("agage", help="folder holding the CFC-11 AGAGE .nc files")
    args = ap.parse_args()
    benchmark(args.f11, args.agage)


if __name__ == "__main__":
    main()
