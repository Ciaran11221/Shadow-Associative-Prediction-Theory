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

## The flag count

One flag is weak. Counting them isn't. [Issue 21](https://github.com/Ciaran11221/Shadow-Associative-Prediction-Theory/issues/21) set a ladder: for any month, how many sources flagged in that month or the 11 before it. A source is one lab's record at one station. The levels stack, so one lab alone stops at level 2 ([issue 23](https://github.com/Ciaran11221/Shadow-Associative-Prediction-Theory/issues/23)).

| Level | Needs | Action |
|---|---|---|
| 1 | 1 source | Log it |
| 2 | 2 or more sources | Worth a look |
| 3 | 3 or more sources from both labs | Escalate |
| 4 | 10 or more sources from both labs, in both hemispheres | Act |

On CFC-11's 18 sources (12 NOAA stations, 5 long AGAGE records and Gosan), the 96 months before 2013 read 62 at level 0, 31 at level 1 and 3 at level 2, with none higher. Level 3 arrives in November 2013, and level 4 in December 2014 with 14 sources. The levels were picked after seeing this, so CFC-11 can't prove them. Code: [scripts/flag_ladder.py](../scripts/flag_ladder.py).

## False flags

A sign only means something if the check stays quiet when nothing is happening. Issue 23 picked 4 banned gases with no reported change before anyone opened their readings, and set the pass mark: none may reach level 3. Code: [scripts/clean_gases.py](../scripts/clean_gases.py). Output: the `clean_` files in [cases/C02](C02/).

**Result: fails. 2 of 4 reached level 3.** That stays on record.

| Gas | Sources tested | Source-months | Flags | Chance alone gives | Top level | Gas-years |
|---|---|---|---|---|---|---|
| Methyl chloroform | 22 | 3,927 | 0 | 7.1 | 0 | 20.5 |
| H-1301 | 22 | 2,076 | 3 | 3.8 | 1 | 12.3 |
| H-1211 | 24 | 4,312 | 11 | 7.8 | 3 | 21.1 |
| H-2402 | 22 | 2,045 | 40 | 3.7 | 4 | 7.9 |

"Chance alone" is 0.182% of tested months, the rate for a straight fall. A gas-year is one gas watched for a year, counting only months where level 3 was possible. That makes 3 level 3 runs in 61.8 gas-years. On the 18 sources CFC-11 had, 1 of 4 reached level 3: H-2402.

Worth a look stays at November 2013. Issue 23 said Gosan could move it to May 2013 only if its measure flagged on none of the 4, and it flagged on 3.

**H-2402 shouldn't have been on the list.** A paper from April 2026 reports its emissions rising since 2015, driven by East Asia (Choi et al.), and an abstract from the same group in April 2024 is the earliest public report found. The test on issue 23 would have put it out. The search leaned on the 2022 WMO assessment and missed it, and the paper turned up only after the run.

In the run, H-2402's fall about halved in both labs between 2010–2015 and 2022–2025: NOAA from 0.0066 to 0.0033 ppt a year, AGAGE from 0.0071 to 0.0039. The ladder reached level 3 in May 2021 and level 4 in September 2022, 35 and 19 months before that abstract. This is an observation, not a result. Nobody set the run up as a test of H-2402, the paper was found after the flags, and April 2024 is the first public date found, not the date anyone first noticed.

**H-1211 is the false alarm.** Its fall is steady and its flags are close to chance. Level 3 came from local things lining up: one-month spikes in NOAA's Wisconsin flasks, a one-month jump at Jungfraujoch that shows on all three halons in May 2021, and a hump at Ragged Point. On CFC-11's 18 sources it never reaches level 3.

**Why the ladder failed.** A count of 3 is too low for 22 to 24 sources over 20 years. On a straight fall with nothing happening, chance alone takes a gas to level 3 6% to 18% of the time, so about 41% of the time at least one of the 4 gets there. That sum should have been done before the pass mark was set. The count stays as it is for now, because 5 gases can't set a new one.

**Limits.**

- A flag says a fall slowed, not why. A bend in a gas's global curve reaches every station in the same years, so two labs can agree on what happened without showing the cause.
- The halons have no combined table, so they use plain monthly averages of flask samples, which aren't smoothed the way CFC-11's table is.
- Only the abstracts of Choi et al. were read.
- Searches after the run found no reported change for H-1211, H-1301 or methyl chloroform. That isn't proof there was none.
- These 4 gases have now been seen, so they can't judge a new version of the ladder.

## Gas events

A check also has to fire when something real happens. [Issue 25](https://github.com/Ciaran11221/Shadow-Associative-Prediction-Theory/issues/25) listed every gas with a published change that both labs could test, and dated the list and the scoring before any of their readings were opened. A [comment on 6 November](https://github.com/Ciaran11221/Shadow-Associative-Prediction-Theory/issues/25#issuecomment-6690511615), also before the run, tightened what counts as a hit. Code: [scripts/gas_events.py](../scripts/gas_events.py). Output: the `events` files in [cases/C02](C02/).

- **Event stretch:** from the month the change began up to the month before the first public date. A hit is the level going from under 3 to 3 or more inside it. A level 3 carried over from before the change doesn't count.
- **Quiet stretch:** from January 2005 up to the month the change began. Level 3 there is a false alarm.
- **Not testable:** fewer than 3 sources, or only one lab, tested in the event stretch.

**Result: 1 hit, 2 misses, 1 not testable, and 1 false alarm in 3 quiet stretches.** That stays on record.

| Gas | Change began | First public date, as dated | Result | First level 3 | Lead | False alarm |
|---|---|---|---|---|---|---|
| Carbon tetrachloride | 2013 | 10 Feb 2021, Park et al. | Hit | Jan 2015 | 73 months | No |
| CFC-12 | 2013 | 10 Feb 2021, Park et al. | Miss | None | None | No |
| HCFC-141b | 2017 | 27 Apr 2022, Western et al. | Miss | None | None | Nov 2011 |
| CFC-115 | 2011 | 10 Oct 2017, Vollmer et al. | Not testable | None | None | None |

CFC-12 and carbon tetrachloride are tied to CFC-11, so the three of them count as one event. Before the run, the code met copies of the real files with every reading replaced by a made-up one, and each planted result read right. After it, a separate program that shares no code agreed on all 12,596 source-months and every outcome.

**How much luck can do.** Before the run, a sum using each source's tested months, and no readings, gave each gas's chance of a hit and of a false alarm from luck alone. Each gas reads against the row nearest its own flag rate in its quiet stretch, a reading set before the run.

| Month flag rate | HCFC-141b | CFC-12 | Carbon tetrachloride |
|---|---|---|---|
| 0.182%, a straight fall | 5.7% / 5.0% | 7.9% / 3.9% | 7.6% / 3.9% |
| 0.305%, noise that carries over | 18.9% / 18.0% | 26.2% / 14.4% | 25.3% / 14.4% |
| 0.472%, CFC-11's own rate before 2013 | 44.2% / 42.2% | 56.0% / 35.9% | 53.9% / 35.9% |

Each cell is a lucky hit, then a lucky false alarm. A level of 3 is a low bar, which is why a single hit proves little.

**Carbon tetrachloride is the hit.** Level 3 came in January 2015 from three sources: NOAA Mauna Loa in March 2014, AGAGE Mace Head from August to October 2014, and AGAGE Samoa in January 2015. Two of those only just cleared the line, at 3.19 and 3.06 times the usual miss, and none of the three flagged on another gas within a month. Its quiet stretch flagged 3 times in 1,324 source-months, 0.227%, which picks the 0.182% row: a lucky hit 7.6% of the time, or 12.8% at its exact rate. The stronger sign is the stretch as a whole. Gosan aside, 68% of readings sat above the line, against 30% in the quiet years, flags came 9 times as often, and a second run at level 3 lasted from December 2017 to October 2019.

**An earlier report turned up after the run.** Lunt et al., online 18 October 2018, reported a new source of carbon tetrachloride in China's Shandong province after 2012. Measured from it, the lead is 45 months, not 73. The scored result stays as dated and this sits beside it, as with H-2402. Park et al. 2018, a discussion paper from March 2018, reported large unreported emissions from China for 2011 to 2015 but not a change, so it isn't counted.

**CFC-12 is a clean miss.** Apart from one Gosan flag in May 2013, its readings sat below the line the whole time: the highest in the event stretch was 1.52 times the usual miss. The extra emissions made its fall a little shallower without ever turning it upward. The rule only sees readings above the line, so a fall that only slows can't flag. That blind spot is now on record.

**HCFC-141b missed, and its false alarm was a real rise.** Gosan aside, only 3% of its readings sat above the line in its event stretch, as issue 25 expected for a gas that was still bending over. The false alarm came in November 2011 from 8 northern sources in both labs within two months, with southern stations following 3 to 22 months later, which is how a change in the air spreads. The 2014 ozone assessment, public on 10 September 2014, reported HCFC-141b emissions rising since the previous assessment, in line with reported production, which peaked again in 2011. So the alert saw a real rise, a legal and reported one, 34 months before that assessment said so. Under the dated rules it stays a false alarm.

**CFC-115 couldn't be tested,** as expected: NOAA's file runs only from January 2010 to August 2015, too short for the 10-year rule. AGAGE stations flagged it 9 times in 2017 before the October paper, but one lab alone stops at level 2.

**Seen in passing, not scored.**

- Gosan flagged CFC-11, CFC-12, carbon tetrachloride and CFC-115 in May 2013, and none of its other four gases that spring. A plume from eastern China fits, and so does a shift in the winds.
- Carbon tetrachloride reached level 3 again from June 2024 to May 2026, and was back at level 2 in June 2026, the latest month. The newest data are often revised.

**Limits.**

- Stations measure at fixed points, so a flag can come from a change in how air is carried to them as well as from emissions. A hit shows timing, not cause.
- The lead runs to the first public report found, not to when anyone first noticed.
- Only the abstracts of Park et al. 2021 and Lunt et al. 2018 were read, and only the summary of the 2014 assessment.
- Quiet stretches keep turning out not to be quiet: H-2402 last time, HCFC-141b now. That makes false alarms look more common than they are.
- These four gases have now been seen, so they can't judge a new version of the ladder.

## Sources

- [Choi et al. 2026, npj Climate and Atmospheric Science](https://doi.org/10.1038/s41612-026-01399-4)
- [Choi et al. 2024, EGU General Assembly abstract](https://doi.org/10.5194/egusphere-egu24-13726)
- [NOAA GML flask data notes, with the papers that first presented these records](https://gml.noaa.gov/aftp/data/hats/halons/flasks/ReadMe.txt)
- [Montzka et al. 2003, Geophysical Research Letters](https://doi.org/10.1029/2003GL017745)
- [Montzka et al. 2018, Nature](https://doi.org/10.1038/s41586-018-0106-2)
- [Lunt et al. 2018, Geophysical Research Letters](https://doi.org/10.1029/2018GL079500)
- [Park et al. 2018, Atmospheric Chemistry and Physics](https://doi.org/10.5194/acp-18-11729-2018)
- [Vollmer et al. 2018, Atmospheric Chemistry and Physics](https://doi.org/10.5194/acp-18-979-2018)
- [Western et al. 2022, Atmospheric Chemistry and Physics](https://doi.org/10.5194/acp-22-9601-2022)
- [WMO/UNEP Scientific Assessment of Ozone Depletion: 2014](https://csl.noaa.gov/assessments/ozone/2014/)
- [Rigby et al. 2019, Nature](https://doi.org/10.1038/s41586-019-1193-4)
- [Park et al. 2021, Nature](https://doi.org/10.1038/s41586-021-03277-w)
- [Chen et al. 2020, JGR Atmospheres](https://doi.org/10.1029/2020JD033051)
- [NOAA combined CFC-11 table](https://doi.org/10.15138/BVQ6-2S69)
- [AGAGE data, version 20260716](https://www-air.larc.nasa.gov/missions/agage/data/)
