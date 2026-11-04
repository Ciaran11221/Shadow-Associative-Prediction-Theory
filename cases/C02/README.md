# Case C02: check it yourself

Everything in [the case file](../C02-cfc11-eastern-china.md) can be rebuilt from NOAA's public table. Run the steps below. Each one says what you should see. If a step gives something else, the write-up is wrong until we know why.

## What's in this folder

| File | What it holds |
|---|---|
| [check.csv](check.csv) | Every month tested from January 2005: reading, line, usual miss, gap and whether it flagged |
| [all_series.csv](all_series.csv) | The same rule on all 16 series, in first-flag order |
| [chart.png](chart.png) | The global reading against the 2002 to 2012 trend |

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

## What these steps don't prove

They show the arithmetic is right and repeatable. They don't remove the limits listed in the case file: the series was picked after seeing the data, all 16 come from one lab, and the table is smoothed.
