---
id: T1
title: Night-time light, then China's coal
law: L3
status: planned
---

# T1. Night-time light, then China's coal

**Tests:** L3, the gap is the signal.

## Stage 1: rebuild a known result

Rebuild the night-lights comparison on free data. Each step fits one sitting and ends with something you can see.

| Step | Do | Done when |
|---|---|---|
| 1.1 | Look for the paper's replication files (Martinez, Journal of Political Economy, 2022) | A link to them is in this file, or a note that there are none |
| 1.2 | Get night-time light per country per year, 1992–2013 | One table: country, year, light |
| 1.3 | Get reported GDP growth per country per year (World Bank) | One table: country, year, growth |
| 1.4 | Get a democracy score per country per year, the one the paper used if it says | One table: country, year, score |
| 1.5 | Join the three tables | One table, with its row count written down and the countries that didn't match listed |
| 1.6 | Run the comparison | One number: how far autocracies' reported growth runs above what their light implies, next to the paper's ~35% |

- **Done when:** step 1.6 lands in the published range (about 35%).
- **If it reads otherwise:** check the pipeline against the paper's replication files, if published, before concluding anything. A real failure to reproduce becomes a case.

## Stage 2: point it at a new target

China's coal use, 2010–2014, using only data public before November 2015. Candidate shadows: power output, steel and cement output, satellite nitrogen dioxide, and the national-versus-provincial totals. Calibrate them on countries with trusted figures, never on China's own (R3).

- **Done when:** the gap flags under-reporting before the November 2015 revision. Known answer: up to 17%, about 600 million tonnes for 2012.
- **If it reads otherwise:** record which shadows missed and why. A shadow that misses a known answer fails PROVEN.

## Not decided yet

- Which democracy score to use.
- Which night-light series (the older one runs 1992–2013).
- The cut-off for "flagged", set and named before the run (R7).

## Sources

- [Becker Friedman Institute summary of Martinez (2022)](https://bfi.uchicago.edu/insight/research-summary/how-much-should-we-trust-the-dictators-gdp-growth-estimates/)
- [Council on Foreign Relations: China recalculates its coal consumption](https://www.cfr.org/blog/china-recalculates-its-coal-consumption-why-really-matters)
- [Guan et al. 2012](https://research-portal.uea.ac.uk/en/publications/the-gigatonne-gap-in-chinas-carbon-dioxide-inventories/)
