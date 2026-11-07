#!/usr/bin/env python3
"""Gas events (issue 25): the flag ladder scored on gases with a published change.

For each gas the event stretch runs from the month the change began up to the month before the
first public date. A hit is the level reaching 3 or higher from under 3 inside that stretch, so a
level 3 that carries on from the month before the change began does not count. The quiet stretch
is every month before the change began; level 3 or higher there is a false alarm.

Usage:
  python scripts/gas_events.py <noaa folder> <agage folder> --out <folder>

Writes the five files of clean_gases.py, plus events.csv with one row per gas.
Standard library, matplotlib and scipy.io.netcdf_file only.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import c02_cfc11 as c  # noqa: E402
import clean_gases as g  # noqa: E402
import flag_ladder as fl  # noqa: E402

# name, NOAA file, kind of NOAA file, AGAGE gas code
EVENT_GASES = [
    ("HCFC-141b", "HCFC141B_GCMS_flask.txt", "gcms", "hcfc-141b"),
    ("CFC-115", "CFC115_M2.txt", "gcms", "cfc-115"),
    ("CFC-12", "HATS_global_F12.txt", "table:F12", "cfc-12"),
    ("carbon tetrachloride", "HATS_global_CCl4.txt", "table:CCl4", "ccl4"),
]

# Issue 25. CFC-12 and carbon tetrachloride are tied to CFC-11, so they share its group.
EVENTS = [
    {"gas": "HCFC-141b", "group": "HCFC-141b", "began": "2017-01", "public": "2022-04-27"},
    {"gas": "CFC-115", "group": "CFC-115", "began": "2011-01", "public": "2017-10-10"},
    {"gas": "CFC-12", "group": "CFC-11", "began": "2013-01", "public": "2021-02-10"},
    {"gas": "carbon tetrachloride", "group": "CFC-11", "began": "2013-01", "public": "2021-02-10"},
]

COLUMNS = ["gas", "group", "began", "first_public", "outcome", "first_level_3", "lead_months",
           "sources_at_first_level_3", "tested_noaa", "tested_agage", "false_alarm",
           "first_false_level_3", "quiet_months", "quiet_months_possible", "quiet_gas_years"]


def month_of(text):
    """'2017-01' or '2022-04-27' -> month index."""
    return c.idx(int(text[:4]), int(text[5:7]))


def first_reach(months, began, public):
    """First month in the stretch (began up to the month before public) at level 3 or higher whose
    previous month in `months` was under 3 (the first month of the list counts as coming from 0).
    Returns the month dict or None. Walks the full list, so it sees the month before the stretch."""
    for k, m in enumerate(months):
        if not began <= m["month"] < public:
            continue
        before = months[k - 1]["level"] if k > 0 else 0
        if m["level"] >= 3 and before < 3:
            return m
    return None


def score(months, sources, event):
    """months: ladder dicts; sources: ladder sources; event: one entry of EVENTS. Returns one dict."""
    began, public = month_of(event["began"]), month_of(event["public"])
    quiet = [m for m in months if m["month"] < began]
    in_stretch = [s for s in sources if any(began <= t < public for t in s.tested)]
    tested_noaa = sum(s.lab == "NOAA" for s in in_stretch)
    tested_agage = sum(s.lab == "AGAGE" for s in in_stretch)
    testable = len(in_stretch) >= 3 and tested_noaa > 0 and tested_agage > 0
    first = first_reach(months, began, public)
    if not testable:
        outcome = "not testable"
    else:
        outcome = "hit" if first else "miss"
    hit = outcome == "hit"
    false_first = fl.first_at(quiet, 3)
    possible = sum(bool(m["possible"]) for m in quiet)
    return {"gas": event["gas"], "group": event["group"], "began": event["began"],
            "first_public": event["public"], "outcome": outcome,
            "first_level_3": c.label(first["month"]) if hit else None,
            "lead_months": public - first["month"] if hit else None,
            "sources_at_first_level_3": first["count"] if hit else None,
            "tested_noaa": tested_noaa, "tested_agage": tested_agage,
            "false_alarm": false_first is not None,
            "first_false_level_3": c.label(false_first["month"]) if false_first else None,
            "quiet_months": len(quiet), "quiet_months_possible": possible,
            "quiet_gas_years": possible / 12}


def closing_lines(rows):
    """The two last lines printed by run, as strings."""
    count = lambda name: sum(r["outcome"] == name for r in rows)  # noqa: E731
    events = len({r["group"] for r in rows})
    possible = sum(r["quiet_months_possible"] > 0 for r in rows)
    alarms = sum(bool(r["false_alarm"]) for r in rows)
    return (f"hits {count('hit')}, misses {count('miss')}, not testable {count('not testable')} "
            f"of {len(rows)} gases, which are {events} separate events",
            f"false alarms {alarms} of {possible} gases where level 3 was possible in the quiet stretch")


def run(noaa_folder, agage_folder, out, gases=EVENT_GASES, events=EVENTS):
    results = g.run(noaa_folder, agage_folder, out, gases)["gases"]
    by_gas = {r["gas"]: r for r in results}
    rows = [score(by_gas[e["gas"]]["months"], by_gas[e["gas"]]["sources"], e) for e in events]
    g.write_csv(Path(out) / "events.csv", COLUMNS, [[g.cell(r[k]) if not isinstance(r[k], bool) else str(r[k]).lower()
                                                     for k in COLUMNS] for r in rows])
    for line in closing_lines(rows):
        print(line)
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("noaa", help="folder holding NOAA's files for the event gases")
    ap.add_argument("agage", help="folder holding the AGAGE .nc files for the event gases")
    ap.add_argument("--out", required=True, help="folder to write the CSV files to")
    args = ap.parse_args()
    run(args.noaa, args.agage, args.out)


if __name__ == "__main__":
    main()
