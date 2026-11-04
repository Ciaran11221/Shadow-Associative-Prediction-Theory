---
id: C02
title: Banned CFC-11 traced to eastern China
year: 2019
laws: [L3]
rules: [R9]
---

# C02. Banned CFC-11 traced to eastern China

**What happened.** CFC-11, an ozone-destroying gas once used in foam insulation, was phased out under the Montreal Protocol, so its emissions should have kept falling. In 2018 scientists reported they had risen since 2012 (Montzka et al., Nature). In 2019, measurements from stations in South Korea and Japan traced much of the rise to eastern China (Rigby et al., Nature). China cracked down, and emissions fell.

**What it shows.** The gap between "banned, so falling" and the measured air was the signal (L3). A treaty meant someone was responsible for acting on it (R9).

## Checked against the data

The rule was set before anyone saw a reading ([issue 16](https://github.com/Ciaran11221/Shadow-Associative-Prediction-Theory/issues/16)): draw a straight line through the previous 10 years, extend it one month, and flag the month if the reading sits more than 3 times the usual miss above the line. Usual miss is how far those 10 years normally sit from their own line. Data: NOAA's combined table, version 2026-06-11. Code: [scripts/c02_cfc11.py](../scripts/c02_cfc11.py). Output: [cases/C02](C02/). To rebuild every number yourself, follow [the steps](C02/README.md).

| Question | Result |
|---|---|
| Did the fall slow after 2012? | Yes. 2.045 ppt a year in 2002–2012, then 1.122 ppt a year in 2013–2017, which is 54.9% of the earlier speed. The rule asked for 40% to 60% |
| How early would the check flag the global average? | August 2014, 45 months before the paper, with no false alarms in the 96 months tested before 2013 |

![Global CFC-11 against the 2002 to 2012 trend](C02/chart.png)

**The margin is thin.** The global result holds only for cut-offs between 2.19 and 3.76 times the usual miss. At 2 times there are 7 false alarms, the first in December 2009. At 4 times nothing flags. The cut-off was set before the data was opened, so the result is fair, but a strong signal wouldn't sit in so narrow a gap.

## Worth a look

Worth a look is the earliest month a check fixed in advance would have put a case in front of a person. It's a marker, not proof.

**November 2013, 54 months before the paper.** The same rule, unchanged, was run once on all 16 series in the table ([all_series.csv](C02/all_series.csv)). Worth a look is the earliest flag from 2013 on a series with no false alarm before it.

| Measurement | North average | Cape Kumukahi, Hawaii |
|---|---|---|
| Reading | 234.403 ppt | 234.329 ppt |
| Where the 10-year line said it should be | 233.389 ppt | 233.254 ppt |
| Gap | +1.014 ppt | +1.075 ppt |
| Cut-off (3 × usual miss) | 0.996 ppt | 1.034 ppt |
| Times the usual miss | 3.06 | 3.12 |

**The cross-check is the order of arrival.** A gas released in the north should show in the north first, then spread south, and it does:

| First flag from 2013 | Where |
|---|---|
| November 2013 | North average, Cape Kumukahi, Niwot Ridge (Colorado) |
| April 2014 | The gap between north and south |
| May 2014 | Trinidad Head (California) |
| August 2014 | Global average, Mauna Loa |
| October to December 2014 | Summit, Pt. Barrow, Alert, Mace Head, Cape Matatula, South Pole, south average |
| January 2016 | Palmer Station (Antarctica) |
| October 2017 | Cape Grim (Tasmania) |

The yearly gap between north and south was 1.83 ppt in 2012, 2.94 in 2014 and 3.11 in 2017, then 1.15 in 2021. It widens with the release and closes after it stops.

**Limits.**

- The series was picked after seeing the data. The rule is unchanged, but 16 tries make an early hit more likely by luck, which is why the order of arrival counts for more than any single date.
- The November 2013 flag is one month, by 0.018 ppt. The north doesn't flag again until September 2014. Niwot Ridge has one false alarm before 2013 and Mauna Loa has five.
- All 16 series come from one lab, so under R2 they count as one source.
- The table is smoothed, so a month's value can borrow from later months and any flag date is approximate. It's on a 2016 calibration scale, so it isn't exactly what anyone saw in 2014.
- A flag says the fall slowed, not why or who. It took measurements in South Korea and Japan to trace it.
- Whether anyone would have acted on a flag isn't measured (R9). Production in eastern China appears to have fallen during 2017–2018 (Park et al. 2021), so the fall can't simply be credited to the May 2018 paper.

**What could move it earlier.** Gases made alongside CFC-11, which rose after 2013 and fell one to two years before it (Park et al. 2021), and NASA's AIRS infrared satellite, whose trends are less negative over Shandong but also over two regions with no known source (Chen et al. 2020). Any earlier date has to come from a check fixed before its data is opened, and tested on gases with no scandal.

## Cross-check: AGAGE

AGAGE is a separate network with its own labs and instruments, so it's the independent angle (L2). The rule was fixed on [issue 18](https://github.com/Ciaran11221/Shadow-Associative-Prediction-Theory/issues/18) before its readings were opened: the same 10-year rule on five long records, and a 5-year line at Gosan, on how far its readings sit above clean air that month, because its record starts in 2007. The pass mark was at least 3 of the 5 long records flagging before May 2018, with no false alarms before 2013.

**First run: no, 2 of 5.** One missing month blocked the next 10 years, so four stations weren't tested in the period that matters. That result stays on record ([agage.csv](C02/agage.csv)).

**Gap rule: yes, 5 of 5.** A new rule was posted on issue 18 before those stations were looked at: a month is tested if at least 90% of its window has readings, the line is fitted through the months that exist, and nothing is filled in ([agage_gaps.csv](C02/agage_gaps.csv)).

| Station | First flag from 2013 | Months before the paper | Times the usual miss | False alarms before 2013 |
|---|---|---|---|---|
| Gosan, South Korea | May 2013 | 60 | 6.13 | No history |
| Trinidad Head, California | November 2013 | 54 | 3.09 | 0 |
| Ragged Point, Barbados | December 2013 | 53 | 3.38 | 0 |
| Mace Head, Ireland | November 2014 | 42 | 3.17 | 0 |
| Cape Matatula, Samoa | December 2016 | 17 | 3.04 | 0 |
| Cape Grim, Tasmania | August 2017 | 9 | 3.03 | 0 |

A separate lab flags in the same month as worth a look, and the station nearest the source flags first.

**Limits.**

- The pass came after a rule change that followed a no, and two of the five stations had already been seen when the change was written.
- The pass mark was loose: two of the five flags came only 17 and 9 months before the paper.
- Gosan's May 2013 is the strongest flag here, but it can't move worth a look yet. Only 45 of its 86 months were tested, and it has no false-alarm history. It needs the same measure run on gases with no scandal.
- Trinidad Head's flag is a narrow one: a gap of 1.38 ppt against a cut-off of 1.339.

## Sources

- [Montzka et al. 2018, Nature](https://doi.org/10.1038/s41586-018-0106-2)
- [Rigby et al. 2019, Nature](https://doi.org/10.1038/s41586-019-1193-4)
- [Park et al. 2021, Nature](https://doi.org/10.1038/s41586-021-03277-w)
- [Chen et al. 2020, JGR Atmospheres](https://doi.org/10.1029/2020JD033051)
- [NOAA combined CFC-11 table](https://doi.org/10.15138/BVQ6-2S69)
- [AGAGE data, version 20260716](https://www-air.larc.nasa.gov/missions/agage/data/)
