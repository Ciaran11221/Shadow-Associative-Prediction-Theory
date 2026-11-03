---
id: T2
title: City air-quality false-alarm filter
law: L2
status: planned
---

# T2. City air-quality false-alarm filter

**Tests:** L2, independent angles pin it down.

Cheap dust sensors read fog as pollution. When a sensor spikes, check it against independent angles: weather (humidity, fog), satellite fire and smoke data, and official monitoring stations.

- **Baseline to beat:** a plain threshold on humidity-corrected readings (the US EPA's correction for PurpleAir sensors).
- **Done when:** on past spikes in one city, the cross-check raises fewer false alarms than the baseline and misses no real event, with official stations as the reference.
- **If it reads otherwise:** extra angles add nothing at city scale; rethink before going bigger.
- **Also measured:** flags per week put in front of a person (R8).

## Not decided yet

- Which city.

## Sources

- [OpenAQ: open air-quality data](https://openaq.org)
- [Sensor.Community: citizen air sensors](https://sensor.community)
- [Open-Meteo: weather data](https://open-meteo.com)
- [NASA FIRMS: fire data](https://firms.modaps.eosdis.nasa.gov)
