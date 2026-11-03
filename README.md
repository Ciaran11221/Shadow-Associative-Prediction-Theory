# Shadow Associative Prediction Theory

**Everything casts a shadow.**

A proposed theory, and the plan for a tool: a multi-angle cross-check that watches public data nobody has time to watch, works out what to trust, and flags what doesn't add up.

> **Status: v0.1, proposed and untested.** Every law below states the result that would prove it wrong. The first test is [T1](tests/T1-night-lights.md).

The shadow is Carl Jung's word for what a person hides or won't see. This theory is about the shadow of the world: what official records hide or never measured. Jung supplied the word, not the evidence ([origins](docs/origins.md)).

**A shadow is an indicator:** something you can measure that moves with something you can't, like night-time light for a country's real economy, or lichens for sulphur in the air. Finding the right one is finding variable X.

## The idea

We've collected more ingredients than any generation before us: satellites, sensors, records. The recipes are scattered, one per paper, in fields that don't read each other. Sometimes the signal is there before the event, in a photograph nobody was looking at. One person can't watch it all. This is designed to.

## Three laws

| Law | Claim | False if |
|---|---|---|
| **L1. Everything casts a shadow** | Anything that happens at scale leaves traces in things measured for other reasons | A search set up in advance finds passing shadows for fewer hidden quantities than its stated threshold |
| **L2. One angle can lie; independent angles pin it down** | Agreement between independent sources (different owners, different methods) is what earns trust | In backtests, agreement is no more accurate than a single source |
| **L3. The gap is the signal** | Where an official number and its shadows disagree, look there first | Flagged gaps predict later corrections no better than chance |

The full statement, definitions, nine working rules and the strongest objections are in [THEORY.md](THEORY.md).

## What's here

| Path | What it holds |
|---|---|
| [THEORY.md](THEORY.md) | The theory: scope, definitions, assumptions, laws, working rules, objections |
| [docs/shadow-test.md](docs/shadow-test.md) | The test every shadow must pass, and the traps |
| [docs/prior-work.md](docs/prior-work.md) | Who has built parts of this already, and what's new here |
| [docs/origins.md](docs/origins.md) | Where the name and the ideas come from |
| [cases/](cases/) | Real events, one file each, tagged with the laws and rules they bear on |
| [shadows/](shadows/) | Known shadows, one file each, scored on the shadow test |
| [tests/](tests/) | Planned tests, one per law, each with the result that would count against it |
| [INDEX.md](INDEX.md) | Generated index of all of the above |
| [STATUS.md](STATUS.md) | Where the theory stands, what's next, and what isn't verified |
| [CHANGELOG.md](CHANGELOG.md) | What changed in each version |
| [scripts/check_corpus.py](scripts/check_corpus.py) | Rebuilds the index; fails if a law has no case or test, or a rule has no case |
| [.github/workflows/check.yml](.github/workflows/check.yml) | Runs that check on every push |
| [LICENSE](LICENSE) | The CC BY 4.0 legal text |

## Cite

GitHub's "Cite this repository" button uses [CITATION.cff](CITATION.cff).

## Licence

Creative Commons Attribution 4.0 International (CC BY 4.0): reuse is welcome, with credit. Full text in [LICENSE](LICENSE).
