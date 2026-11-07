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
Compare-Object (Get-Content "$env:TEMP\c02-check\events-outy_year.csv") (Get-Content "cases\C02\events_by_year.csv")
```

As before, a newer version of the files may shift these numbers, and `checks.csv` isn't kept here because it's about 2.6 MB and can be rebuilt.

## What these steps don't prove

They show the arithmetic is right and repeatable. They don't remove the limits listed in the case file: the series was picked after seeing the data, all 16 come from one lab, and the table is smoothed. The clean gases were picked before their readings were opened, but one of them turned out not to be clean. The event gases were picked and scored before their readings were opened too, but their first public dates are the first found, and one turned out to have an earlier report.
