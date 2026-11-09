---
id: S14
title: Gas levels in remote clean air, for hidden emissions
real: yes
proven: yes
useful: history
---

# S14. Gas levels in remote clean air, for hidden emissions

| Field | Value |
|---|---|
| Hidden quantity | Emissions of a gas that nobody reports, or reports wrongly |
| Shadow | Monthly levels of the gas at remote stations, measured by two separate networks, NOAA and AGAGE, to track the ozone layer and the climate |
| Why it moves | Gas released anywhere mixes through the air, so more emissions make the level fall more slowly or rise faster than before |
| Other causes | Changes in winds and in how air reaches a station, a source next to one station, instrument and calibration changes, and the gas's own lifetime |
| Calibrated on | Models that work back from the levels to emissions, checked against reported inventories |
| Speed | Monthly readings. A change shows first near its source and reaches the far half of the world months later ([C02](../cases/C02-cfc11-eastern-china.md)) |
| Record | Decades of monthly readings from both networks |

**Known result.** CFC-11 fell more slowly from 2012, which revealed emissions nobody had reported (Montzka et al., Nature, 2018). Measurements in South Korea and Japan traced much of them to eastern China (Rigby et al., Nature, 2019), and emissions there fell after action was taken (Park et al., Nature, 2021).

**As an early alert, not yet.** In this repo ([C02](../cases/C02-cfc11-eastern-china.md)), a rule fixed before looking flags CFC-11 from November 2013 on today's files, 54 months before the 2018 paper. That's shown, not proven: the rule was shaped on CFC-11, and the files have been revised since. A count of 3 stations failed its false-alarm test. The bursts test on 16 new gases found 17 bursts that build up and stay, but they didn't line up with known changes more often than chance. No alert rule on this shadow has passed a test on events it wasn't built from.

## Sources

- [Montzka et al. 2018, Nature](https://doi.org/10.1038/s41586-018-0106-2)
- [Rigby et al. 2019, Nature](https://doi.org/10.1038/s41586-019-1193-4)
- [Park et al. 2021, Nature](https://doi.org/10.1038/s41586-021-03277-w)
- [NOAA combined CFC-11 table](https://doi.org/10.15138/BVQ6-2S69)
- [AGAGE data, version 20260716](https://www-air.larc.nasa.gov/missions/agage/data/)
