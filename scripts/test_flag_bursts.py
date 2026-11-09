"""Tests for scripts/flag_bursts.py and the reader changes in clean_gases.py. Made-up data only, in temp folders."""
import contextlib
import csv
import io
import json
import math
import sys
import unittest
from decimal import Decimal, getcontext
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import c02_cfc11 as c  # noqa: E402
import clean_gases as g  # noqa: E402
import flag_bursts as fb  # noqa: E402
import flag_ladder as fl  # noqa: E402
from test_clean_gases import (AGAGE_CODES, FROM, H1301_HEAD, NOAA_CODES, Base, h1301_row,  # noqa: E402
                              monthly_rows, straight, write_nc, write_table)
from test_gas_events import table_lines  # noqa: E402


def span(first, last):
    return range(c.idx(*first), c.idx(*last) + 1)


def src(lab, code, flags=(), tested=span((2010, 1), (2013, 12))):
    return fl.make_source(lab, code, flags, tested)


def jan(year, n):
    """n flagged months in a year: January onward."""
    return [c.idx(year, m) for m in range(1, n + 1)]


def exact_tail(k, lam):
    """P(X >= k) summed upward in 60 digit decimals, as an independent check."""
    getcontext().prec = 60
    lam = Decimal(str(lam))
    term = (-lam).exp() * lam ** k / math.factorial(k)
    total = Decimal(0)
    for j in range(k, k + 300):
        total += term
        term = term * lam / (j + 1)
    return total


class GasYears(unittest.TestCase):
    def one(self, flags_by_year=(), tested=span((2010, 1), (2013, 12))):
        flags = [m for y, n in dict(flags_by_year).items() for m in jan(y, n)]
        return fb.gas_years([src("NOAA", "a", flags, tested)])

    def test_a_year_with_11_tested_source_months_does_not_count(self):
        rows = self.one(tested=list(span((2010, 1), (2010, 11))) + list(span((2011, 1), (2013, 12))))
        self.assertEqual([r["year"] for r in rows], [2011, 2012, 2013])

    def test_the_first_2_counting_years_are_not_judged(self):
        rows = self.one()
        self.assertEqual([(r["year"], r["judged"]) for r in rows],
                         [(2010, False), (2011, False), (2012, True), (2013, True)])
        self.assertIsNone(rows[0]["chance"])

    def test_the_third_counting_year_is_judged_with_a_usual_rate_from_the_first_two(self):
        rows = self.one({2010: 1, 2011: 3, 2012: 9})
        r = rows[2]
        self.assertEqual(r["usual_rate"], 4 / 24)
        self.assertEqual(r["expected"], 12 * 4 / 24)
        self.assertEqual(r["flags"], 9)

    def test_the_usual_rate_uses_all_earlier_years_not_only_the_last_two(self):
        rows = self.one({2010: 6, 2011: 0, 2012: 0, 2013: 1})
        self.assertEqual(rows[3]["usual_rate"], 6 / 36)

    def test_no_flags_earlier_gives_the_floor_not_0(self):
        rows = self.one({2012: 2})
        self.assertEqual(rows[2]["usual_rate"], 0.00182)
        self.assertAlmostEqual(rows[2]["expected"], 12 * 0.00182)

    def test_changing_a_later_years_flags_changes_no_earlier_verdict(self):
        a = self.one({2010: 1, 2011: 1, 2012: 3, 2013: 0})
        b = self.one({2010: 1, 2011: 1, 2012: 3, 2013: 9})
        self.assertEqual(a[:3], b[:3])
        self.assertNotEqual(a[3]["chance"], b[3]["chance"])
        fb.mark_bursts({"x": a})
        fb.mark_bursts({"x": b})
        self.assertEqual([r["burst"] for r in a[:3]], [r["burst"] for r in b[:3]])

    def test_the_tail_of_5_flags_when_half_a_flag_is_expected(self):
        got, want = fb.poisson_tail(5, 0.5), float(exact_tail(5, 0.5))
        self.assertLess(abs(got - want) / want, 1e-9)
        self.assertAlmostEqual(got, 1.7211e-4, places=7)

    def test_the_tail_of_1_flag_is_1_minus_e_to_the_minus_the_mean(self):
        want = 1 - math.exp(-0.5)
        self.assertLess(abs(fb.poisson_tail(1, 0.5) - want) / want, 1e-12)

    def test_a_tiny_tail_is_not_lost_to_rounding(self):
        got, want = fb.poisson_tail(30, 0.01), float(exact_tail(30, 0.01))
        self.assertGreater(got, 0)
        self.assertLess(abs(got - want) / want, 1e-9)
        self.assertEqual(fb.poisson_tail(0, 3.0), 1.0)

    def test_a_chance_just_under_and_just_over_the_bar_is_a_burst_and_not(self):
        bar = 0.05 / 2

        def rows(chance):
            return [{"judged": True, "chance": chance}, {"judged": True, "chance": 0.9},
                    {"judged": False, "chance": None}]
        under, over = rows(bar * (1 - 1e-6)), rows(bar * (1 + 1e-6))
        self.assertEqual(fb.mark_bursts({"x": under})[0], 2)  # 2 judged, the unjudged one is not counted
        self.assertTrue(under[0]["burst"])
        fb.mark_bursts({"x": over})
        self.assertFalse(over[0]["burst"])
        self.assertFalse(under[2]["burst"])

    def test_the_bar_divides_by_the_years_judged_across_all_gases(self):
        a = [{"judged": True, "chance": 0.001}] * 3 + [{"judged": False, "chance": None}] * 5
        b = [{"judged": True, "chance": 0.04}] * 7
        n, bar = fb.mark_bursts({"a": [dict(r) for r in a], "b": [dict(r) for r in b]})
        self.assertEqual((n, bar), (10, 0.005))


class Stretches(unittest.TestCase):
    def test_a_year_with_one_month_inside_is_inside(self):
        self.assertTrue(fb.stretch_flags("SF6", 2020)["inside"])           # only Jan and Feb 2020 are in the stretch
        self.assertFalse(fb.stretch_flags("SF6", 2023)["inside"])
        one = [("up", ["X"], "2010-12", "2011-02")]
        self.assertTrue(fb.stretch_flags("X", 2010, one)["inside"])
        self.assertTrue(fb.stretch_flags("X", 2011, one)["inside"])
        self.assertFalse(fb.stretch_flags("X", 2012, one)["inside"])
        self.assertFalse(fb.stretch_flags("X", 2009, one)["inside"])

    def test_stretch_ends_are_inclusive(self):
        end = [("up", ["X"], "2008-06", "2009-01")]
        self.assertTrue(fb.stretch_flags("X", 2009, end)["inside"])        # January 2009 is the last month
        self.assertFalse(fb.stretch_flags("X", 2010, end)["inside"])

    def test_a_year_touching_only_a_down_stretch_is_down_only(self):
        f = fb.stretch_flags("HFC-152a", 2007)
        self.assertEqual((f["inside"], f["down_only"], f["no_stretch"], f["touches_up"]), (False, True, False, False))
        f = fb.stretch_flags("HCFC-22", 2014)
        self.assertEqual((f["inside"], f["down_only"]), (False, True))

    def test_a_down_year_that_also_touches_an_up_or_instrument_stretch_is_inside_not_down_only(self):
        f = fb.stretch_flags("HFC-152a", 2008)  # down all year, instrument from July
        self.assertEqual((f["inside"], f["down_only"], f["touches_up"]), (True, False, False))
        f = fb.stretch_flags("HCFC-22", 2012)   # down from Jan 2011, up until June 2012
        self.assertEqual((f["inside"], f["down_only"], f["touches_up"]), (True, False, True))

    def test_2008_for_hfc_227ea_is_inside_from_the_instrument_stretch(self):
        f = fb.stretch_flags("HFC-227ea", 2008)
        self.assertEqual((f["inside"], f["touches_up"]), (True, False))
        self.assertEqual([s[0] for s in fb.stretches_touched("HFC-227ea", 2008)], ["instrument"])

    def test_2008_for_nitrous_oxide_is_not_inside(self):
        f = fb.stretch_flags("Nitrous oxide", 2008)
        self.assertEqual((f["inside"], f["no_stretch"]), (False, True))

    def test_a_year_touching_no_stretch_is_no_stretch(self):
        f = fb.stretch_flags("Methyl bromide", 2015)
        self.assertEqual((f["inside"], f["down_only"], f["no_stretch"]), (False, False, True))


def yrow(inside, burst=False, down_only=False, no_stretch=False, up=False, judged=True):
    return {"judged": judged, "inside": inside, "burst": burst, "down_only": down_only,
            "no_stretch": no_stretch, "touches_up": up}


class Question1(unittest.TestCase):
    def planted(self):
        return {"A": [yrow(True, burst=k < 5) for k in range(10)] + [yrow(False, no_stretch=True) for _ in range(10)]}

    def test_a_gas_with_only_inside_years_is_not_eligible(self):
        q = fb.question_1({"A": [yrow(True, burst=True) for _ in range(6)]}, shuffles=50)
        self.assertEqual((q["eligible_gases"], q["verdict"], q["chance"]), (0, "not judged", None))

    def test_a_gas_with_only_1_outside_year_is_not_eligible(self):
        rows = [yrow(True) for _ in range(5)] + [yrow(False)]
        self.assertEqual(fb.question_1({"A": rows}, shuffles=50)["eligible_gases"], 0)

    def test_a_gas_with_1_inside_and_3_outside_judged_years_is_not_eligible(self):
        rows = [yrow(True, burst=True)] + [yrow(False) for _ in range(3)]
        self.assertEqual(fb.question_1({"A": rows}, shuffles=50)["eligible_gases"], 0)

    def test_with_0_shuffles_the_chance_is_exactly_1(self):
        q = fb.question_1(self.planted(), shuffles=0)
        self.assertEqual(q["eligible_gases"], 1)
        self.assertEqual(q["chance"], 1.0)

    def test_a_ratio_of_1_5_fails_even_with_a_chance_under_0_05(self):
        # 40 gases, each 10 inside years with 6 bursts and 10 outside years with 4: 240 of 400 against 160 of 400
        rows = {f"G{k}": [yrow(True, burst=j < 6) for j in range(10)] + [yrow(False, burst=j < 4) for j in range(10)]
                for k in range(40)}
        q = fb.question_1(rows, shuffles=1000)
        self.assertAlmostEqual(q["ratio"], 1.5)
        self.assertLess(q["chance"], 0.05)
        self.assertEqual(q["verdict"], "fail")

    def test_a_gas_with_only_inside_years_and_3_bursts_adds_nothing_to_the_totals(self):
        base = self.planted()
        extra = dict(base, B=[yrow(True, burst=True) for _ in range(3)])
        a, b = fb.question_1(base, shuffles=50), fb.question_1(extra, shuffles=50)
        self.assertEqual(b["bursts_inside"], a["bursts_inside"])
        self.assertEqual((b["inside_years"], b["bursts_outside"]), (a["inside_years"], a["bursts_outside"]))

    def test_unjudged_years_are_not_counted(self):
        rows = [yrow(True) for _ in range(2)] + [yrow(False) for _ in range(2)] + [yrow(None, judged=False)] * 9
        q = fb.question_1({"A": rows}, shuffles=50)
        self.assertEqual((q["eligible_gases"], q["inside_years"], q["outside_years"]), (1, 2, 2))

    def test_bursts_all_inside_with_rate_outside_0_count_as_a_ratio_of_2_or_more(self):
        q = fb.question_1(self.planted())
        self.assertEqual((q["bursts_inside"], q["bursts_outside"], q["rate_outside"]), (5, 0, 0.0))
        self.assertEqual(q["ratio"], math.inf)
        self.assertEqual(q["verdict"], "pass")

    def test_the_same_seed_twice_gives_the_same_chance(self):
        a, b = fb.question_1(self.planted(), seed=7), fb.question_1(self.planted(), seed=7)
        self.assertEqual(a["chance"], b["chance"])

    def test_a_planted_case_has_a_chance_in_the_right_range(self):
        # 5 bursts on 10 inside and 10 outside years: all 5 inside has chance C(10,5) / C(20,5) = 252 / 15504 = 0.01625
        q = fb.question_1(self.planted())
        self.assertGreater(q["chance"], 0.010)
        self.assertLess(q["chance"], 0.023)
        self.assertEqual(q["shuffles"], 10000)

    def test_bursts_spread_evenly_fail(self):
        rows = [yrow(k % 2 == 0, burst=k in (0, 1, 2, 3)) for k in range(20)]
        q = fb.question_1({"A": rows})
        self.assertEqual((q["verdict"], q["ratio"]), ("fail", 1.0))

    def test_a_big_ratio_with_a_chance_over_0_05_fails(self):
        rows = [yrow(True, burst=True)] + [yrow(True) for _ in range(5)] + [yrow(False) for _ in range(6)]
        q = fb.question_1({"A": rows})
        self.assertGreater(q["chance"], 0.05)
        self.assertEqual(q["verdict"], "fail")

    def test_a_shuffle_stays_inside_one_gas(self):
        # gas A: all its years inside; B: all but 2 of its years inside, bursts only in B's inside years
        a = {"A": [yrow(True, burst=True) for _ in range(5)] + [yrow(False) for _ in range(5)],
             "B": [yrow(True) for _ in range(5)] + [yrow(False) for _ in range(5)]}
        q = fb.question_1(a, shuffles=2000)
        # A's 5 bursts land on 5 of its 10 years: P(all inside) = 1/252, so the chance is far under a mix across gases
        self.assertLess(q["chance"], 0.01)


def flagged_sources(by_source, gas="A", year=2010, others=()):
    """by_source: {'NOAA a': [months in year]}; others: {gas: {'NOAA a': [months]}} for other gases.
    -> sources_by_gas. Every source tested all year."""
    def make(spec):
        out = []
        for sid, months in spec.items():
            lab, code = sid.split()
            out.append(src(lab, code, [c.idx(year, m) for m in months], span((year, 1), (year, 12))))
        return out
    sbg = {gas: make(by_source)}
    for name, spec in dict(others).items():
        sbg[name] = make(spec)
    return sbg


class Builds(unittest.TestCase):
    def test_4_sources_both_labs_top_share_0_3_is_air(self):
        sbg = flagged_sources({"NOAA a": [1, 2, 3], "NOAA b": [4, 5, 6], "AGAGE c": [7, 8], "AGAGE d": [9, 10]})
        build, d = fb.build_of("A", 2010, sbg)
        self.assertEqual(build, "air")
        self.assertAlmostEqual(d["top_share"], 0.3)

    def test_3_sources_in_one_lab_is_unsorted(self):
        sbg = flagged_sources({"NOAA a": [1], "NOAA b": [2], "NOAA c": [3]})
        self.assertEqual(fb.build_of("A", 2010, sbg)[0], "unsorted")

    def test_4_sources_both_labs_but_one_has_half_or_more_is_not_air(self):
        sbg = flagged_sources({"NOAA a": [1, 2, 3, 4, 5, 6], "NOAA b": [7], "AGAGE c": [8], "AGAGE d": [9]})
        self.assertNotEqual(fb.build_of("A", 2010, sbg)[0], "air")

    def test_one_source_with_70_percent_flagging_2_other_gases_is_one_station_many_gases(self):
        mine = {"NOAA x": [1, 2, 3, 4, 5, 6, 7], "NOAA b": [8], "AGAGE c": [9], "AGAGE d": [10]}
        sbg = flagged_sources(mine, others={"B": {"NOAA x": [3]}, "C": {"NOAA x": [7]}, "D": {"NOAA x": [12]}})
        build, d = fb.build_of("A", 2010, sbg)
        self.assertEqual((build, d["station"]), ("one station, many gases", "NOAA x"))
        self.assertAlmostEqual(d["top_share"], 0.7)

    def test_one_source_with_70_percent_and_no_other_gas_is_one_station_one_gas(self):
        mine = {"NOAA x": [1, 2, 3, 4, 5, 6, 7], "NOAA b": [8], "AGAGE c": [9], "AGAGE d": [10]}
        sbg = flagged_sources(mine, others={"B": {"NOAA x": [12]}, "C": {"NOAA y": [3]}})  # wrong month, wrong source
        self.assertEqual(fb.build_of("A", 2010, sbg)[0], "one station, one gas")

    def test_one_source_with_70_percent_and_exactly_1_other_gas_is_unsorted(self):
        mine = {"NOAA x": [1, 2, 3, 4, 5, 6, 7], "NOAA b": [8], "AGAGE c": [9], "AGAGE d": [10]}
        sbg = flagged_sources(mine, others={"B": {"NOAA x": [3]}, "C": {"NOAA x": [12]}})
        self.assertEqual(fb.build_of("A", 2010, sbg)[0], "unsorted")

    def test_two_sources_tied_at_50_percent_is_unsorted(self):
        sbg = flagged_sources({"NOAA x": [1, 2, 3, 4, 5], "AGAGE y": [6, 7, 8, 9, 10]})
        self.assertEqual(fb.build_of("A", 2010, sbg)[0], "unsorted")

    def test_3_sources_both_labs_flagging_2_1_1_has_one_alone_at_half_so_one_station_one_gas(self):
        sbg = flagged_sources({"NOAA a": [1, 2], "NOAA b": [3], "AGAGE c": [4]})
        build, d = fb.build_of("A", 2010, sbg)
        self.assertEqual((build, d["top_share"], d["station"]), ("one station, one gas", 0.5, "NOAA a"))

    def test_flags_in_another_year_are_not_counted(self):
        sbg = {"A": [src("NOAA", "x", [c.idx(2010, 1), c.idx(2011, 1), c.idx(2011, 2)], span((2010, 1), (2011, 12)))]}
        self.assertEqual(fb.flagged_months(sbg["A"], 2010), {"NOAA x": [c.idx(2010, 1)]})


def burst(gas, build, up):
    return {"gas": gas, "build": build, "touches_up": up}


class Question2(unittest.TestCase):
    def test_4_air_bursts_is_void(self):
        bursts = [burst("A", "air", True) for _ in range(4)] + [burst("A", "one station, one gas", False) for _ in range(6)]
        q = fb.question_2(bursts, shuffles=100)
        self.assertEqual((q["verdict"], q["air_bursts"], q["chance"]), ("void", 4, None))

    def test_4_station_bursts_is_void(self):
        bursts = [burst("A", "air", True) for _ in range(6)] + [burst("A", "one station, many gases", False) for _ in range(4)]
        self.assertEqual(fb.question_2(bursts, shuffles=100)["verdict"], "void")

    def test_a_planted_pass_is_a_pass(self):
        # air all inside up stretches, stations all outside: the chance is 1 / C(16, 8) before rounding up to 1 / 10001
        bursts = [burst("A", "air", True) for _ in range(8)] + [burst("A", "one station, one gas", False) for _ in range(8)]
        q = fb.question_2(bursts)
        self.assertEqual((q["air_share"], q["station_share"], q["ratio"]), (1.0, 0.0, math.inf))
        self.assertLess(q["chance"], 0.01)
        self.assertEqual(q["verdict"], "pass")

    def test_labels_are_the_same_everywhere_so_it_fails(self):
        bursts = [burst("A", "air", k % 2 == 0) for k in range(8)] + [burst("A", "one station, one gas", k % 2 == 0) for k in range(8)]
        self.assertEqual(fb.question_2(bursts, shuffles=500)["verdict"], "fail")

    def test_an_air_share_of_1_5_times_the_station_share_fails_even_with_a_chance_under_0_05(self):
        # 40 gases, each 5 air bursts (3 inside up stretches) and 5 station bursts (2 inside): 0.6 against 0.4
        bursts = []
        for k in range(40):
            bursts += [burst(f"G{k}", "air", j < 3) for j in range(5)]
            bursts += [burst(f"G{k}", "one station, one gas", j < 2) for j in range(5)]
        q = fb.question_2(bursts, shuffles=1000)
        self.assertAlmostEqual(q["ratio"], 1.5)
        self.assertLess(q["chance"], 0.05)
        self.assertEqual(q["verdict"], "fail")

    def test_unsorted_bursts_are_in_neither_share(self):
        bursts = ([burst("A", "air", True) for _ in range(5)] + [burst("A", "one station, one gas", False) for _ in range(5)]
                  + [burst("A", "unsorted", True) for _ in range(9)])
        q = fb.question_2(bursts, shuffles=100)
        self.assertEqual((q["air_bursts"], q["station_bursts"]), (5, 5))

    def test_the_same_seed_twice_gives_the_same_chance(self):
        bursts = [burst("A" if k % 2 else "B", "air" if k % 3 else "one station, one gas", k % 4 < 2) for k in range(24)]
        self.assertEqual(fb.question_2(bursts, seed=3)["chance"], fb.question_2(bursts, seed=3)["chance"])

    def test_labels_swap_only_inside_one_gas(self):
        # gas A holds every air burst and gas B every station burst: no swap can cross, so the shares never change
        bursts = [burst("A", "air", True) for _ in range(6)] + [burst("B", "one station, one gas", False) for _ in range(6)]
        q = fb.question_2(bursts, shuffles=300)
        self.assertEqual(q["chance"], 1.0)  # every shuffle ties the observed difference
        self.assertEqual(q["verdict"], "fail")


class DownCheck(unittest.TestCase):
    def test_9_down_only_years_is_not_judged(self):
        rows = {"A": [yrow(False, down_only=True) for _ in range(9)] + [yrow(False, no_stretch=True) for _ in range(9)]}
        d = fb.down_check(rows, shuffles=50)
        self.assertEqual((d["verdict"], d["down_only_years"], d["chance"]), ("not judged", 9, None))

    def test_10_down_only_years_are_judged(self):
        rows = {"A": [yrow(False, down_only=True) for _ in range(10)] + [yrow(False, no_stretch=True) for _ in range(10)]}
        self.assertEqual(fb.down_check(rows, shuffles=50)["verdict"], "ok")

    def test_pooled_across_gases_a_down_only_rate_not_above_the_no_stretch_rate_is_ok(self):
        # A: 6 bursts, all in its 20 down only years (0.3). B: 10 no stretch years, all bursts. Pooled no stretch 10 of 30.
        rows = {"A": [yrow(False, down_only=True, burst=k < 6) for k in range(20)]
                + [yrow(False, no_stretch=True) for _ in range(20)],
                "B": [yrow(False, no_stretch=True, burst=True) for _ in range(10)]}
        d = fb.down_check(rows, shuffles=1000)
        self.assertEqual((d["down_only_years"], d["down_only_bursts"], d["no_stretch_years"], d["no_stretch_bursts"]),
                         (20, 6, 30, 10))
        self.assertLess(d["rate_down_only"], d["rate_no_stretch"])
        self.assertLess(d["chance"], 0.05)  # so the ok comes from the rates, not the chance
        self.assertEqual(d["verdict"], "ok")

    def test_bursts_piled_into_down_only_years_say_check_the_rule(self):
        rows = {"A": [yrow(False, down_only=True, burst=k < 6) for k in range(10)]
                + [yrow(False, no_stretch=True) for _ in range(10)]}
        d = fb.down_check(rows)
        self.assertLess(d["chance"], 0.05)
        self.assertEqual(d["verdict"], "check the rule or the list")


def gml_lines(tag, stations=NOAA_CODES):
    names = [f"GML_{tag}_YYYY", f"GML_{tag}_MM"]
    for agg in ("NH", "SH", "Global"):
        names += [f"GML_{agg}_{tag}", f"GML_{agg}_{tag}_sd"]
    for code in stations:
        names += [f"GML_{code}_{tag}", f"GML_{code}_{tag}_sd"]
    names.append(f"GML_{tag}_Programs")
    rows = []
    for i in range(c.idx(2000, 1), c.idx(2000, 6) + 1):
        y, m = c.ym(i)
        rows.append("  ".join([str(y), str(m)] + ["1.000", "0.100"] * 3 + ["2.000", "0.100"] * len(stations) + ["1"]))
    return ["# made up"] * 3 + ["  ".join(names)] + rows, names


class Readers(Base):
    def test_gml_table_with_prefix_gml_and_tag_sf6_gives_12_stations(self):
        lines, names = gml_lines("SF6")
        self.assertEqual(len(names), 33)
        p = self.file("sf6.txt", lines)
        for d in (g.read_table(p, "SF6", "GML"), g.noaa_data(self.dir, "sf6.txt", "table:GML:SF6")):
            self.assertEqual(sorted(d), sorted(NOAA_CODES))
            self.assertEqual(len(d), 12)
            self.assertEqual(set(d["alt"].values()), {2.0})  # not the 1.000 of NH, SH or Global
            for key in ("NH", "SH", "Global", "Programs"):
                self.assertNotIn(key, d)
                self.assertNotIn(key.lower(), d)
            self.assertFalse([k for k in d if "_sd" in k or "sd" == k])

    def test_the_gml_prefix_does_not_read_hats_columns_and_the_reverse(self):
        lines, _ = gml_lines("N2O")
        p = self.file("n2o.txt", lines)
        with self.assertRaises(SystemExit):
            g.read_table(p, "N2O")  # prefix HATS: no HATS_N2O_YYYY column

    def test_plain_table_and_table_f12_read_as_they_did(self):
        p = self.dir / "t.txt"
        write_table(p, {code: straight() for code in NOAA_CODES})
        self.assertEqual(g.noaa_data(self.dir, "t.txt", "table"), g.read_table(p))
        self.assertEqual(g.noaa_data(self.dir, "t.txt", "table:MC"), g.read_table(p, "MC"))
        lines, _ = table_lines("F12")
        self.file("f12.txt", lines)
        same = g.read_table(self.dir / "f12.txt", "F12")
        self.assertEqual(len(same), 12)
        self.assertEqual(g.noaa_data(self.dir, "f12.txt", "table:F12"), same)
        self.assertEqual(g.noaa_data(self.dir, "f12.txt", "table:HATS:F12"), same)

    def m2pr1_file(self, rows):
        return self.file("m2.txt", ["# comment"] * 26 + [H1301_HEAD] + rows)

    def test_an_m2pr1_file_with_2_flagged_rows_leaves_both_out_and_counts_them(self):
        p = self.m2pr1_file([h1301_row("ALT", "10.0", "PR1"), h1301_row("ALT", "99.0", "PR1", day="20100116", flag="*"),
                             h1301_row("BRW", "7.0", "M2", day="20100117", flag="N")])
        data, left = g.read_m2pr1(p)
        self.assertEqual(left, 2)
        self.assertEqual(data, {"alt": {c.idx(2010, 1): 10.0}})
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(g.noaa_data(self.dir, "m2.txt", "m2pr1"), data)
        self.assertIn("2 rows", buf.getvalue())

    def test_an_m2pr1_file_with_no_flagged_rows_counts_0_and_keeps_the_pr1_rule(self):
        p = self.m2pr1_file([h1301_row("ALT", "10.0", "M2"), h1301_row("ALT", "20.0", "PR1")])
        data, left = g.read_m2pr1(p)
        self.assertEqual((left, data["alt"][c.idx(2010, 1)]), (0, 20.0))
        self.assertEqual(g.read_h1301(p), data)

    def test_the_h1301_kind_with_a_flagged_row_still_stops(self):
        p = self.m2pr1_file([h1301_row("ALT", "10.0", "PR1", flag="*")])
        with self.assertRaises(SystemExit):
            g.read_h1301(p)
        with self.assertRaises(SystemExit):
            g.noaa_data(self.dir, "m2.txt", "h1301")


class Tables(unittest.TestCase):
    def test_burst_gases_are_exactly_the_16_rows(self):
        self.assertEqual(fb.BURST_GASES, [
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
        ])

    def test_stretches_are_exactly_the_rows(self):
        thirteen = ["HCFC-22", "HCFC-142b", "HFC-134a", "HFC-152a", "HFC-32", "HFC-125", "HFC-143a", "HFC-227ea",
                    "HFC-365mfc", "Methyl bromide", "Methyl chloride", "Perchloroethylene", "Dichloromethane"]
        self.assertEqual(fb.STRETCHES, [
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
            ("instrument", thirteen, "2008-07", "2009-06"),
            ("instrument", ["SF6"], "2021-01", "2022-12"),
            ("instrument", ["CFC-113"], "2023-10", "2024-12"),
        ])
        self.assertEqual(len(thirteen), 13)

    def test_every_stretch_gas_is_one_of_the_16(self):
        names = {row[0] for row in fb.BURST_GASES}
        for _, gases, _, _ in fb.STRETCHES:
            self.assertLessEqual(set(gases), names)


GML_HEAD_TAG = "SF6"
SF6_GAS = ("SF6", "GML_global_SF6.txt", "table:GML:SF6", "sf6")


def write_gml_table(path, series, tag=GML_HEAD_TAG):
    names = [f"GML_{tag}_YYYY", f"GML_{tag}_MM"]
    for agg in ("NH", "SH", "Global"):
        names += [f"GML_{agg}_{tag}", f"GML_{agg}_{tag}_sd"]
    for code in series:
        names += [f"GML_{code}_{tag}", f"GML_{code}_{tag}_sd"]
    names.append(f"GML_{tag}_Programs")
    lines = ["# made up"] * 3 + ["  ".join(names)]
    for i in range(FROM, c.idx(2018, 12) + 1):
        y, m = c.ym(i)
        row = [str(y), str(m)] + ["1.000", "0.100"] * 3
        for fn in series.values():
            row += [f"{fn(i - FROM):.6f}", "0.100"]
        lines.append("  ".join(row + ["1"]))
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


class EndToEnd(Base):
    def setUp(self):
        super().setUp()
        self.noaa, self.agage, self.out = self.dir / "noaa", self.dir / "agage", self.dir / "out"
        self.noaa.mkdir()
        self.agage.mkdir()

    def go(self, jump_noaa=("alt", "brw"), jump_agage=("mhd", "thd"), month=c.idx(2012, 6), **kw):
        j = month - FROM
        write_gml_table(self.noaa / "GML_global_SF6.txt",
                        {code: straight(k, jump_at=j if code in jump_noaa else None) for k, code in enumerate(NOAA_CODES)})
        for k, code in enumerate(AGAGE_CODES):
            write_nc(self.agage / f"agage_{code}_sf6_monthly-baseline-20260716.nc",
                     monthly_rows(straight(k + 3, jump_at=j if code in jump_agage else None)))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            result = fb.run(self.noaa, self.agage, self.out, [SF6_GAS], **kw)
        return result, buf.getvalue().strip().splitlines()

    def read(self, name):
        with open(self.out / name, newline="") as fh:
            return list(csv.DictReader(fh))

    def test_a_jump_at_4_sources_in_both_labs_in_one_year_inside_a_stretch_bursts_as_air(self):
        result, lines = self.go()
        self.assertEqual([b["year"] for b in result["main"]["bursts"]], [2012])
        row = next(r for r in self.read("bursts.csv") if r["year"] == "2012")
        self.assertEqual((row["flags"], row["judged"], row["burst"], row["inside"], row["build"]),
                         ("4", "true", "true", "true", "air"))
        self.assertEqual(sum(r["burst"] == "true" for r in self.read("bursts.csv")), 1)
        entry = json.loads((self.out / "library" / "sf6-2012.json").read_text(encoding="utf-8"))
        self.assertEqual((entry["gas"], entry["year"], entry["flags"], entry["build"]), ("SF6", 2012, 4, "air"))
        self.assertEqual(sorted(entry["labs"]), ["AGAGE", "NOAA"])
        self.assertEqual(len(entry["sources"]), 4)
        self.assertEqual(entry["first_flag_north"], "2012-06")
        self.assertIsNone(entry["first_flag_south"])
        self.assertEqual(entry["stretches"], ["up 2008-01 to 2020-02"])
        self.assertNotIn("seen", entry)
        self.assertTrue(lines[-4].startswith("bursts 1 in 12 gas years judged, bar 0.00417"))

    def test_the_last_4_lines_and_the_files(self):
        _, lines = self.go()
        self.assertEqual([x.split(":")[0].split(" ")[0] for x in lines[-4:]], ["bursts", "question", "question", "down"])
        self.assertTrue(lines[-3].startswith("question 1: inside "))
        self.assertTrue(lines[-3].endswith("not judged"))
        self.assertTrue(lines[-2].startswith("question 2: air 1 of 1 inside up stretches, one station 0 of 0"))
        self.assertTrue(lines[-2].endswith("void"))
        self.assertTrue(lines[-1].startswith("down check: down only 0 bursts in 0 years"))
        for name in ("checks.csv", "sources.csv", "months.csv", "by_year.csv", "summary.csv", "bursts.csv", "questions.csv"):
            self.assertTrue((self.out / name).exists(), name)
        rows = {(r["question"], r["item"]): r["value"] for r in self.read("questions.csv")}
        self.assertEqual(rows[("bursts", "gas_years_judged")], "12")
        self.assertEqual(rows[("question 1", "verdict")], "not judged")
        self.assertEqual(rows[("question 2", "verdict")], "void")
        header = list(self.read("bursts.csv")[0])
        self.assertEqual(header, fb.BURST_COLUMNS)

    def test_no_burst_when_nothing_jumps(self):
        result, lines = self.go(jump_noaa=(), jump_agage=())
        self.assertEqual(result["main"]["bursts"], [])
        self.assertTrue(lines[-4].startswith("bursts 0 in 12 gas years judged"))
        self.assertEqual(list((self.out / "library").glob("*.json")), [])

    def test_a_seen_burst_goes_in_the_library_marked_seen_and_counts_in_nothing(self):
        # an earlier run, on methyl chloroform, with a jump at 4 sources in 2010
        earlier_noaa, earlier_agage, earlier_out = self.dir / "e_noaa", self.dir / "e_agage", self.dir / "e_out"
        earlier_noaa.mkdir()
        earlier_agage.mkdir()
        j = c.idx(2010, 6) - FROM
        write_table(earlier_noaa / "HATS_global_MC.txt",
                    {code: straight(k, jump_at=j if code in ("alt", "brw") else None) for k, code in enumerate(NOAA_CODES)})
        for k, code in enumerate(AGAGE_CODES):
            write_nc(earlier_agage / f"agage_{code}_ch3ccl3_monthly-baseline-20260716.nc",
                     monthly_rows(straight(k + 3, jump_at=j if code in ("mhd", "thd") else None)))
        with contextlib.redirect_stdout(io.StringIO()):
            g.run(earlier_noaa, earlier_agage, earlier_out, [("methyl chloroform", "HATS_global_MC.txt", "table", "ch3ccl3")])
        plain, plain_lines = self.go()
        shutil_rmtree(self.out)
        seen, seen_lines = self.go(seen_files=[earlier_out / "checks.csv"])
        self.assertEqual(plain_lines[-4:], seen_lines[-4:])
        self.assertEqual(len(seen["main"]["bursts"]), 1)
        entry = json.loads((self.out / "library" / "seen1-methyl-chloroform-2010.json").read_text(encoding="utf-8"))
        self.assertTrue(entry["seen"])
        self.assertEqual((entry["flags"], entry["build"], entry["stretches"]), (4, "air", []))
        self.assertTrue((self.out / "library" / "sf6-2012.json").exists())
        self.assertEqual(sum(r["burst"] == "true" for r in self.read("bursts.csv")), 1)  # the seen burst is not in bursts.csv

    def test_a_seen_run_named_hcfc_22_lists_no_stretches_though_the_main_run_has_some(self):
        earlier_noaa, earlier_agage, earlier_out = self.dir / "e_noaa", self.dir / "e_agage", self.dir / "e_out"
        earlier_noaa.mkdir()
        earlier_agage.mkdir()
        j = c.idx(2010, 6) - FROM
        write_table(earlier_noaa / "HATS_global_MC.txt",
                    {code: straight(k, jump_at=j if code in ("alt", "brw") else None) for k, code in enumerate(NOAA_CODES)})
        for k, code in enumerate(AGAGE_CODES):
            write_nc(earlier_agage / f"agage_{code}_ch3ccl3_monthly-baseline-20260716.nc",
                     monthly_rows(straight(k + 3, jump_at=j if code in ("mhd", "thd") else None)))
        with contextlib.redirect_stdout(io.StringIO()):
            g.run(earlier_noaa, earlier_agage, earlier_out, [("HCFC-22", "HATS_global_MC.txt", "table", "ch3ccl3")])
        self.assertTrue(fb.stretches_touched("HCFC-22", 2010))  # the main run's list does apply to this gas and year
        self.go(seen_files=[earlier_out / "checks.csv"])
        entry = json.loads((self.out / "library" / "seen1-hcfc-22-2010.json").read_text(encoding="utf-8"))
        self.assertTrue(entry["seen"])
        self.assertEqual((entry["gas"], entry["year"], entry["stretches"]), ("HCFC-22", 2010, []))


def shutil_rmtree(path):
    import shutil
    shutil.rmtree(path)


class SeenFiles(Base):
    def test_checks_csv_gives_back_the_sources_with_their_tested_and_flagged_months(self):
        p = self.file("checks.csv", [
            "gas,source,month,reading,line_value,usual_miss,gap,threshold,multiple,flag,skipped,skip_reason",
            "G,NOAA alt,2010-01,1,1,,,,,false,false,",
            "G,NOAA alt,2010-02,1,1,,,,,true,false,",
            "G,NOAA alt,2010-03,,,,,,,skipped,true,gap",
            "G,AGAGE cgo,2010-01,1,1,,,,,false,false,"])
        out = fb.sources_from_checks(p)
        self.assertEqual(list(out), ["G"])
        alt, cgo = out["G"]
        self.assertEqual((alt.id, alt.lab, sorted(alt.tested), sorted(alt.flags)),
                         ("NOAA alt", "NOAA", [c.idx(2010, 1), c.idx(2010, 2)], [c.idx(2010, 2)]))
        self.assertEqual((cgo.lab, cgo.south), ("AGAGE", True))


if __name__ == "__main__":
    unittest.main()
