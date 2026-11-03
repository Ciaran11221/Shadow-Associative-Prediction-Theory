# Status

**v0.1.1, 3 November 2026: proposed, untested.** DOI for all versions: [10.5281/zenodo.23903518](https://doi.org/10.5281/zenodo.23903518)

| | |
|---|---|
| Stated | 3 laws, 9 working rules, 16 cases, 13 shadows (2 of them failures kept on record), 3 planned tests |
| Run | No tests yet |
| Archived | v0.1.1 on Zenodo; every release gets its own DOI |
| Next | T1 step 1.1: look for the paper's replication files |

Work happens in bursts, so every step says what done looks like, and any burst can start from the next step here.

Changes reach `main` only through a pull request, and only once the corpus check passes. That holds for everyone, the owner included.

## Next steps

Tests come first. How much each source counts is measured from their results, so weighting waits until they've run.

1. **T1 stage 1: rebuild the night-lights result, in six steps** ([tests/T1](tests/T1-night-lights.md)). Start at step 1.1. Done when step 1.6 lands in the published range (about 35%). If it reads otherwise, compare against the paper's replication files, if published, before concluding anything.
2. **T1 stage 2: China's coal, 2010–2014.** Done when, using only data public before November 2015, the gap between reported coal use and its shadows flags under-reporting. Known answer: up to 17%. If it reads otherwise, record which shadows missed and why.
3. **T2: the city-air false-alarm filter** ([tests/T2](tests/T2-city-air.md)). Done when, on past spikes in one city, the cross-check raises fewer false alarms than the baseline and misses no real event. If it reads otherwise, extra angles add nothing at city scale; rethink before going bigger. It also records each angle's calls, which step 4 needs.
4. **Weight each source by its track record, like a vote** (the issue of that name). Waits on test results. A weight is how often a source has been right, so it can't be set in advance, and each field needs its own: a source that's good for city air can be poor for coal figures. Done when one field's weights are measured from its results and THEORY.md shows how L2 uses them, with a worked example. If the weights don't beat giving every source the same weight, on results they weren't measured from, they aren't earning their place.

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
