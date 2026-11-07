# Status

**v0.1.1, 3 November 2026: proposed, untested.** DOI for all versions: [10.5281/zenodo.23903518](https://doi.org/10.5281/zenodo.23903518)

| | |
|---|---|
| Stated | 3 laws, 9 working rules, 16 cases, 13 shadows (2 of them failures kept on record), 3 planned tests |
| Run | One proven case checked against data: CFC-11, worth a look November 2013. Its flag count failed on gases picked as clean, then caught 1 of 3 testable gas events. T1, T2 and T3 not run yet |
| Archived | v0.1.1 on Zenodo; every release gets its own DOI |
| Next | Bursts of flags: whether a burst of false flags marks something real |

Work happens in bursts, so every step says what done looks like, and any burst can start from the next step here.

Changes reach `main` only through a pull request, and only once the corpus check passes. That holds for everyone, the owner included.

## Next steps

Proven cases come first: real events where the truth is now known. For each one, look only at what was public before the truth came out. If a sign was already there, write down what it was, where it was and how early. If not, the case counts against the theory. T1's 35% is an estimate nobody has admitted, so T1 waits until these are done.

Tests follow. How much each source counts is measured from their results, so weighting waits until they've run.

1. **CFC-11, the banned gas ([C02](cases/C02-cfc11-eastern-china.md)).** NOAA's table shows the fall slowed, and a check set in advance puts worth a look at November 2013, 54 months before the May 2018 paper. AGAGE, a separate network, agrees under the gap rule. The flag count then failed on gases picked as clean: 2 of 4 reached level 3, and one of the two turned out to have a published rise. Five gases can't set a new count, so examples come first and the fix comes last. Accuracy is two numbers: how many real events get flagged, and how many quiet records do. On gases with a published change it caught carbon tetrachloride early and missed CFC-12 and HCFC-141b.
   1. **More gas events: done.** 1 hit, 2 misses, 1 not testable, and 1 false alarm in 3 quiet stretches ([C02](cases/C02-cfc11-eastern-china.md#gas-events)). Carbon tetrachloride reached level 3 45 to 73 months before the first reports. CFC-12 never rose above the line, because the rule can't see a fall that only slows. HCFC-141b missed, and its false alarm matches a real rise reported in 2014.
   2. **Bursts of flags.** A run of false flags far above the usual rate may mark something real: a change in the air, a fault in an instrument, or a source next to one station. Done when the bar is set by a chance sum and dated on an issue before it runs on gases nobody has looked at, and the share of bursts with a known cause is written down. If bursts line up with known causes no more often than chance, the idea goes.
   3. **First-human dates.** Done when each event has the date people first noticed it, as well as the date of the paper. If that date can't be found, the case says so.
   4. **The replacement gas.** If illegal CFC-11 pushed out legal HCFC-141b, the legal gas should bend the other way at about the same time. Done when a mirrored rule is dated and run. If it doesn't bend, the case says so.
   5. **A blind test,** with names and dates hidden and decoys added. Done when the calls are locked before the reveal and scored on lead time, false alarms and direction.
   6. **A new flag count,** set on those examples and judged on ones it never saw. Done when it's dated and its rate is written down. If it doesn't beat the old count, the old result stands.
2. **Volkswagen ([C04](cases/C04-volkswagen-test-cheat.md)).** Done when the road-test figures from the 2014 report sit next to the US limit in the case file, with the date they became public. If the report doesn't show that gap, the case file is wrong and gets corrected.
3. **Chernobyl ([C01](cases/C01-chernobyl-1986.md)).** Done when the case file has a dated timeline from primary sources: what Sweden's Forsmark plant measured, how it ruled out its own reactors, and when Moscow spoke. If the sources don't support that order of events, the case file gets corrected.
4. **T1 stage 1: rebuild the night-lights result, in six steps** ([tests/T1](tests/T1-night-lights.md)). Parked at step 1.2. Step 1.1 is done: the paper's replication files are linked there. Done when step 1.6 lands in the published range (about 35%). If it reads otherwise, compare against the paper's replication files before concluding anything.
5. **T1 stage 2: China's coal, 2010–2014.** Done when, using only data public before November 2015, the gap between reported coal use and its shadows flags under-reporting. Known answer: up to 17%. If it reads otherwise, record which shadows missed and why.
6. **T2: the city-air false-alarm filter** ([tests/T2](tests/T2-city-air.md)). Done when, on past spikes in one city, the cross-check raises fewer false alarms than the baseline and misses no real event. If it reads otherwise, extra angles add nothing at city scale; rethink before going bigger. It also records each angle's calls, which step 8 needs.
7. **T3: the time-boxed shadow search** ([tests/T3](tests/T3-shadow-search.md)). This is where large numbers of variables belong, so it comes after the blind test, with size going up in steps and a measured false-alarm rate at each. Done when the hit rate meets or beats the threshold written down first. If it reads otherwise, L1 weakens, and the kinds of quantity with no usable shadow get recorded.
8. **Weight each source by its track record, like a vote** (the issue of that name). Waits on test results. A weight is how often a source has been right, so it can't be set in advance, and each field needs its own: a source that's good for city air can be poor for coal figures. Done when one field's weights are measured from its results and THEORY.md shows how L2 uses them, with a worked example. If the weights don't beat giving every source the same weight, on results they weren't measured from, they aren't earning their place.

## Not verified

These came from secondary sources or general reference works and should be checked against the originals before any formal publication.

- **C13:** the 72–99% false-alarm range is quoted from reviews citing Sendelbach & Funk (2013); the original paper wasn't checked.
- **C07:** the 2018 engineer's report and the repair timeline come from general reporting.
- **C11:** Netflix's 2010 cancellation of a second contest.
- **C14, C15, C16, S03, S07:** rest on general reference sources.
- **Origins:** the date of the thief case Jung described in a 1934 lecture wasn't confirmed.
- **S05:** the 32% coverage figure comes from a preprint.
- **S08:** 1.5 billion birds is the authors' scaled estimate, not a count.
- **Zenodo:** one release (v0.1.1) has been archived so far; later releases should work the same way but haven't been tried.
- **C02:** worth a look was picked after seeing the data, all 16 series come from one lab, and NOAA's table is smoothed. Only abstracts of the papers were read, including Choi et al. 2026 on H-2402, Park et al. 2021 and Lunt et al. 2018, and only the summary of the 2014 assessment. The gas events' first public dates are the first found, and carbon tetrachloride's turned out to have an earlier one.
