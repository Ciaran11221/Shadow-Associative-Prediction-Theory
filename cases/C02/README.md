# Case C02: check it yourself

Everything in [the case file](../C02-cfc11-eastern-china.md) can be rebuilt from NOAA's public table. Run the steps below. Each one says what you should see. If a step gives something else, the write-up is wrong until we know why.

## What's in this folder

| File | What it holds |
|---|---|
| [check.csv](check.csv) | Every month tested from January 2005: reading, line, usual miss, gap and whether it flagged |
| [all_series.csv](all_series.csv) | The same rule on all 16 series, in first-flag order |
| [chart.png](chart.png) | The global reading against the 2002 to 2012 trend |
| [agage.csv](agage.csv) | The AGAGE check under the first rule: no, 2 of 5 |
| [agage_gaps.csv](agage_gaps.csv) | The AGAGE check under the gap rule: yes, 5 of 5 |
| [clean_summary.csv](clean_summary.csv) | The false-flag run, one row per gas |
| [clean_sources.csv](clean_sources.csv) | The false-flag run, one row per source: months tested, flags, first and last flag |
| [clean_months.csv](clean_months.csv) | The false-flag run, one row per month: level, count and which sources |
| [clean_by_year.csv](clean_by_year.csv) | Months at each level, per gas per year |
| [events.csv](events.csv) | The gas events run, one row per gas: outcome, first level 3, lead and false alarm |
| [events_summary.csv](events_summary.csv) | The gas events run, one row per gas, in the same columns as the clean run |
| [events_sources.csv](events_sources.csv) | The gas events run, one row per source: months tested, flags, first and last flag |
| [events_months.csv](events_months.csv) | The gas events run, one row per month: level, count and which sources |
| [events_by_year.csv](events_by_year.csv) | Months at each level, per event gas per year |
| [bursts.csv](bursts.csv) | The bursts run, one row per gas year: tested source-months, flags, usual rate, expected, chance, burst, and its kind |
| [bursts_questions.csv](bursts_questions.csv) | The bursts run's three answers: Question 1, Question 2 and the down check |
| [bursts_summary.csv](bursts_summary.csv) | The bursts run, one row per gas, in the same columns as the clean run |
| [bursts_sources.csv](bursts_sources.csv) | The bursts run, one row per source: months tested, flags, first and last flag |
| [bursts_months.csv](bursts_months.csv) | The bursts run, one row per month: level, count and which sources |
| [bursts_by_year.csv](bursts_by_year.csv) | Months at each level, per bursts gas per year |
| [bursts_library/](bursts_library/) | One file per burst: sources and months, labs, north or south first, kind and known changes. Files starting `seen` come from earlier runs and count in nothing |

## Steps

You need Python 3 with matplotlib. Open Windows PowerShell in the top folder of this repo.

**1. Make a working folder.**

```powershell
New-Item -ItemType Directory -Force "$env:TEMP\c02-check"
```

**2. Download NOAA's table.** About 180 KB.

```powershell
Invoke-WebRequest -Uri "https://gml.noaa.gov/aftp/data/hats/cfcs/cfc11/combined/HATS_global_F11.txt" -OutFile "$env:TEMP\c02-check\HATS_global_F11.txt" -UseBasicParsing
```

**3. Check it's the same file.**

```powershell
(Get-FileHash "$env:TEMP\c02-check\HATS_global_F11.txt" -Algorithm SHA256).Hash
```

You should see `1DF921C10A1B4CB76FE3E3DED1D35DA25D580010A53F481FECAE2BFE0E5162C8`. That's NOAA's version of 11 June 2026. If NOAA has published a newer one, the fingerprint will differ and the numbers may shift a little.

**4. Run the tests.** These use made-up data only.

```powershell
python scripts/test_c02_cfc11.py
```

You should see `Ran 9 tests` and `OK`.

**5. Run the check on the real table.**

```powershell
python scripts/c02_cfc11.py "$env:TEMP\c02-check\HATS_global_F11.txt" --out "$env:TEMP\c02-check\out"
```

You should see:

| Line | Value |
|---|---|
| Slope, 2002 to 2012 | −2.045 ppt a year |
| Slope, 2013 to 2017 | −1.122 ppt a year |
| Second as a percent of the first | 54.87, in band |
| First flag month, global | 2014-08 |
| Flags before January 2013 | 0 |
| Total flags, skips | 9, 0 |
| Outcome | visible early |
| Worth a look | 2013-11, 54 months before the paper: north, kum |

**6. Compare with the files in this folder.** Each of these prints nothing if the files match.

```powershell
Compare-Object (Get-Content "$env:TEMP\c02-check\out\all_series.csv") (Get-Content "cases\C02\all_series.csv")
```

```powershell
Compare-Object (Get-Content "$env:TEMP\c02-check\out\check.csv") (Get-Content "cases\C02\check.csv")
```

## AGAGE steps

You also need scipy for these.

**7. Download AGAGE's eight files.** About 390 KB, as a zip.

```powershell
Invoke-WebRequest -Uri "https://www-air.larc.nasa.gov/missions/agage/api/data/download/10151,10155,10152,10153,10146,10149,10059,10071" -OutFile "$env:TEMP\c02-check\agage.zip" -UseBasicParsing
```

```powershell
Expand-Archive -Force "$env:TEMP\c02-check\agage.zip" "$env:TEMP\c02-check\agage"
```

**8. Run the check.**

```powershell
python scripts/c02_agage.py "$env:TEMP\c02-check\agage" --out "$env:TEMP\c02-check\agage-out"
```

You should see the first rule end in `no, 2 of 5`, and the gap rule end in `yes, 5 of 5`.

**9. Compare with the files in this folder.** Each of these prints nothing if the files match.

```powershell
Compare-Object (Get-Content "$env:TEMP\c02-check\agage-out\agage.csv") (Get-Content "cases\C02\agage.csv")
```

```powershell
Compare-Object (Get-Content "$env:TEMP\c02-check\agage-out\agage_gaps.csv") (Get-Content "cases\C02\agage_gaps.csv")
```

AGAGE updates its files, so these ids will point to version 20260716 only for as long as AGAGE keeps it.

## Flag count steps

**10. Run the tests.** These use made-up data only.

```powershell
python scripts/test_flag_ladder.py
```

```powershell
python scripts/test_clean_gases.py
```

You should see `Ran 20 tests` and `Ran 29 tests`, each with `OK`.

**11. Rebuild the ladder on CFC-11.** This uses the files from steps 2 and 7.

```powershell
python scripts/flag_ladder.py "$env:TEMP\c02-check\HATS_global_F11.txt" "$env:TEMP\c02-check\agage"
```

You should see 62, 31, 3, 0 and 0 for levels 0 to 4 before 2013, then level 3 first in 2013-11 and level 4 first in 2014-12.

**12. Download the clean gas files.** About 6.8 MB. AGAGE allows 35 files at a time, so there are two zips.

```powershell
New-Item -ItemType Directory -Force "$env:TEMP\c02-check\clean-noaa", "$env:TEMP\c02-check\clean-agage"
```

```powershell
Invoke-WebRequest -Uri "https://www-air.larc.nasa.gov/missions/agage/api/data/download/11175,11173,11168,11172,11171,11174,11167,11176,11169,11166,11170,11095,11106,11256,11254,11248,11249,11253,11252,11255,11257,11250,11247,11251,11179,11190,11322" -OutFile "$env:TEMP\c02-check\clean1.zip" -UseBasicParsing
```

```powershell
Invoke-WebRequest -Uri "https://www-air.larc.nasa.gov/missions/agage/api/data/download/11314,11320,11323,11316,11315,11319,11318,11321,11313,11317,11260,11271,10833,10831,10826,10824,10834,10827,10832,10828,10825,10830,10829,10823,10822,10713,10726" -OutFile "$env:TEMP\c02-check\clean2.zip" -UseBasicParsing
```

```powershell
Expand-Archive -Force "$env:TEMP\c02-check\clean1.zip" "$env:TEMP\c02-check\clean-agage"
```

```powershell
Expand-Archive -Force "$env:TEMP\c02-check\clean2.zip" "$env:TEMP\c02-check\clean-agage"
```

```powershell
foreach ($f in "solvents/CH3CCl3/combined/HATS_global_MC.txt", "halons/flasks/HAL1211_GCMS_flask.txt", "halons/flasks/Hal2402_GCMS_flask.txt", "halons/flasks/H-1301_M2_PR1_MS_flask.txt") { Invoke-WebRequest -Uri "https://gml.noaa.gov/aftp/data/hats/$f" -OutFile "$env:TEMP\c02-check\clean-noaa\$(Split-Path $f -Leaf)" -UseBasicParsing }
```

**13. Run the check.**

```powershell
python scripts/clean_gases.py "$env:TEMP\c02-check\clean-noaa" "$env:TEMP\c02-check\clean-agage" --out "$env:TEMP\c02-check\clean-out"
```

You should see `gases reaching level 3: 2 of 4`, `gases reaching level 3 on the CFC-11 set: 1 of 4` and `gosan flagged on: H-1211, H-1301, H-2402`.

**14. Compare with the files in this folder.** Each of these prints nothing if the files match.

```powershell
Compare-Object (Get-Content "$env:TEMP\c02-check\clean-out\summary.csv") (Get-Content "cases\C02\clean_summary.csv")
```

```powershell
Compare-Object (Get-Content "$env:TEMP\c02-check\clean-out\sources.csv") (Get-Content "cases\C02\clean_sources.csv")
```

```powershell
Compare-Object (Get-Content "$env:TEMP\c02-check\clean-out\months.csv") (Get-Content "cases\C02\clean_months.csv")
```

```powershell
Compare-Object (Get-Content "$env:TEMP\c02-check\clean-out\by_year.csv") (Get-Content "cases\C02\clean_by_year.csv")
```

NOAA and AGAGE update their files, so a newer version may shift these numbers. The run also writes `checks.csv`, every tested month with its reading. That file isn't kept here, because it's about 3 MB and can be rebuilt.

## Gas events steps

**15. Run the tests.** These use made-up data only.

```powershell
python scripts/test_gas_events.py
```

You should see `Ran 42 tests` and `OK`.

**16. Download the event gas files.** About 4.7 MB. AGAGE allows 35 files at a time, so there are two zips.

```powershell
New-Item -ItemType Directory -Force "$env:TEMP\c02-check\events-noaa", "$env:TEMP\c02-check\events-agage"
```

```powershell
Invoke-WebRequest -Uri "https://www-air.larc.nasa.gov/missions/agage/api/data/download/10476,10474,10477,10377,10469,10470,10467,10475,10471,10468,10472,10466,10473,10465,9987,9988,9985,9981,9888,9980,9978,9986,9982,9979,9976,9983" -OutFile "$env:TEMP\c02-check\events1.zip" -UseBasicParsing
```

```powershell
Invoke-WebRequest -Uri "https://www-air.larc.nasa.gov/missions/agage/api/data/download/9977,9984,10371,10369,10372,10365,10363,10306,10364,10368,10367,10370,10362,10366,11622,11620,11614,11542,11615,11619,11618,11621,11616,11623,11613,11617" -OutFile "$env:TEMP\c02-check\events2.zip" -UseBasicParsing
```

```powershell
Expand-Archive -Force "$env:TEMP\c02-check\events1.zip" "$env:TEMP\c02-check\events-agage"
```

```powershell
Expand-Archive -Force "$env:TEMP\c02-check\events2.zip" "$env:TEMP\c02-check\events-agage"
```

```powershell
foreach ($f in "cfcs/cfc12/combined/HATS_global_F12.txt", "solvents/CCl4/combined/HATS_global_CCl4.txt", "hcfcs/hcfc141b/HCFC141B_GCMS_flask.txt", "cfcs/cfc115/CFC115_M2.txt") { Invoke-WebRequest -Uri "https://gml.noaa.gov/aftp/data/hats/$f" -OutFile "$env:TEMP\c02-check\events-noaa\$(Split-Path $f -Leaf)" -UseBasicParsing }
```

**17. Run the scoring.**

```powershell
python scripts/gas_events.py "$env:TEMP\c02-check\events-noaa" "$env:TEMP\c02-check\events-agage" --out "$env:TEMP\c02-check\events-out"
```

You should see `hits 1, misses 2, not testable 1 of 4 gases, which are 3 separate events` and `false alarms 1 of 3 gases where level 3 was possible in the quiet stretch`.

**18. Compare with the files in this folder.** Each of these prints nothing if the files match.

```powershell
Compare-Object (Get-Content "$env:TEMP\c02-check\events-out\events.csv") (Get-Content "cases\C02\events.csv")
```

```powershell
Compare-Object (Get-Content "$env:TEMP\c02-check\events-out\summary.csv") (Get-Content "cases\C02\events_summary.csv")
```

```powershell
Compare-Object (Get-Content "$env:TEMP\c02-check\events-out\sources.csv") (Get-Content "cases\C02\events_sources.csv")
```

```powershell
Compare-Object (Get-Content "$env:TEMP\c02-check\events-out\months.csv") (Get-Content "cases\C02\events_months.csv")
```

```powershell
Compare-Object (Get-Content "$env:TEMP\c02-check\events-out\by_year.csv") (Get-Content "cases\C02\events_by_year.csv")
```

As before, a newer version of the files may shift these numbers, and `checks.csv` isn't kept here because it's about 2.6 MB and can be rebuilt.

## Bursts steps

**19. Run the tests.** These use made-up data only.

```powershell
python scripts/test_flag_bursts.py
```

You should see `Ran 67 tests` and `OK`.

**20. Download the bursts files.** About 20 MB: 178 AGAGE files in 6 zips, as AGAGE allows 35 files at a time, and 16 NOAA files.

```powershell
New-Item -ItemType Directory -Force "$env:TEMP\c02-check\bursts-noaa", "$env:TEMP\c02-check\bursts-agage", "$env:TEMP\c02-check\bursts-zips"
```

```powershell
$n = 0; foreach ($ids in "10234,10235,10159,10236,10237,10238,10239,10240,10241,10242,10243,11772,11773,11707,11774,11775,11776,11777,11778,11779,11780,11781,11782,11694,11695,11626,11696,11697,11698,11699,11700,11701,11702,11703,11704", "11932,11933,11866,11934,11935,11936,11937,11938,11939,11940,11941,12084,12085,12013,12086,12087,12088,12089,12090,12091,12092,12093,12094,12417,12418,12361,12419,12420,12421,12422,12423,12424,12425,12426,12427", "11853,11854,11785,11855,11856,11857,11858,11859,11860,11861,11862,11863,12000,12001,11944,12002,12003,12004,12005,12006,12007,12008,12009,12010,12151,12152,12153,12154,12155,12156,12157,12158,12159,12160,12488", "12489,12490,12491,12492,12493,12494,12495,12496,12735,12736,12679,12737,12738,12739,12740,12741,12742,12743,12744,12745,12616,12617,12618,12619,12620,12621,12622,10698,10699,10630,10700,10701,10702,10703,10704", "10705,10706,10707,10708,10905,10906,10837,10907,10908,10909,10910,10911,10912,10913,10914,10915,9874,9875,9876,9877,9878,9879,9880,9881,9882,9883,10617,10618,10546,10619,10620,10621,10622,10623,10624", "10625,10626,10627") { $n++; Invoke-WebRequest -Uri "https://www-air.larc.nasa.gov/missions/agage/api/data/download/$ids" -OutFile "$env:TEMP\c02-check\bursts-zips\bursts$n.zip" -UseBasicParsing; Expand-Archive -Force "$env:TEMP\c02-check\bursts-zips\bursts$n.zip" "$env:TEMP\c02-check\bursts-agage" }
```

```powershell
foreach ($f in "cfcs/cfc113/combined/HATS_global_F113.txt", "hcfcs/hcfc22/flasks/HCFC22_GCMS_flask.txt", "hcfcs/hcfc142b/flasks/HCFC142B_GCMS_flask.txt", "hfcs/hfc134a_GCMS_flask.txt", "hfcs/hf152a_GCMS_flask.txt", "hfcs/HFC-32_M2_PR1_MS_flask.txt", "hfcs/HFC-125_M2_PR1_MS_flask.txt", "hfcs/HFC-143a_M2_PR1_MS_flask.txt", "hfcs/HFC-227ea_GCMS_flask.txt", "hfcs/HFC-365mfc_GCMS_flask.txt", "sf6/combined/GML_global_SF6.txt", "n2o/combined/GML_global_N2O.txt", "methylhalides/ch3br/flasks/CH3BR_GCMS_flask.txt", "methylhalides/ch3cl/flasks/CH3Cl_GCMS_flask.txt", "solvents/C2Cl4/flasks/pce_GCMS_flask.txt", "solvents/CH2Cl2/flasks/ch2cl2_GCMS_flask.txt") { Invoke-WebRequest -Uri "https://gml.noaa.gov/aftp/data/hats/$f" -OutFile "$env:TEMP\c02-check\bursts-noaa\$(Split-Path $f -Leaf)" -UseBasicParsing }
```

**21. Run the bursts test.**

```powershell
python scripts/flag_bursts.py "$env:TEMP\c02-check\bursts-noaa" "$env:TEMP\c02-check\bursts-agage" --out "$env:TEMP\c02-check\bursts-out"
```

It should end with these 4 lines:

- `bursts 17 in 271 gas years judged, bar 0.000185`
- `question 1: inside 9 bursts in 98 years, outside 5 in 131, ratio 2.406, chance 0.3184, fail`
- `question 2: air 4 of 9 inside up stretches, one station 1 of 3, ratio n/a, chance n/a, void`
- `down check: down only 0 bursts in 11 years, no stretch 8 in 162, chance 1.0000, ok`

**22. Compare with the files in this folder.** Each of these prints nothing if the files match.

```powershell
Compare-Object (Get-Content "$env:TEMP\c02-check\bursts-out\bursts.csv") (Get-Content "cases\C02\bursts.csv")
```

```powershell
Compare-Object (Get-Content "$env:TEMP\c02-check\bursts-out\questions.csv") (Get-Content "cases\C02\bursts_questions.csv")
```

```powershell
Compare-Object (Get-Content "$env:TEMP\c02-check\bursts-out\summary.csv") (Get-Content "cases\C02\bursts_summary.csv")
```

```powershell
Compare-Object (Get-Content "$env:TEMP\c02-check\bursts-out\sources.csv") (Get-Content "cases\C02\bursts_sources.csv")
```

```powershell
Compare-Object (Get-Content "$env:TEMP\c02-check\bursts-out\months.csv") (Get-Content "cases\C02\bursts_months.csv")
```

```powershell
Compare-Object (Get-Content "$env:TEMP\c02-check\bursts-out\by_year.csv") (Get-Content "cases\C02\bursts_by_year.csv")
```

The library files match the ones here, apart from the 12 starting `seen`: those come from the same run with `--seen` pointed at the earlier runs' check files and CFC-11's own files. `checks.csv` isn't kept here because it's about 12 MB and can be rebuilt.

## What these steps don't prove

They show the arithmetic is right and repeatable. They don't remove the limits listed in the case file: the series was picked after seeing the data, all 16 come from one lab, and the table is smoothed. The clean gases were picked before their readings were opened, but one of them turned out not to be clean. The event gases were picked and scored before their readings were opened too, but their first public dates are the first found, and one turned out to have an earlier report. The bursts gases were picked and their rules dated before their readings were opened as well, but the years counted as quiet weren't checked as quiet.
