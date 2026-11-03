# Shadow Associative Prediction Theory

**Everything casts a shadow.**

Version 0.1, 2 November 2026. Status: proposed, untested. Each law states the result that would prove it wrong; the tests are planned in [tests/](tests/).

## 1. Summary

Most of the physical world leaves traces that can be turned into data, and decisions get better the more of the picture you can see. This theory reads public data from many fields (air, energy, the economy, health) from several angles at once, and trusts no source alone. When something can't be measured directly, or whoever owns the number hides or bends it, the theory looks for its shadow: a different, measurable quantity that moves with it, the way night-time light moves with economic activity and lichens retreat as sulphur dioxide rises. Where an official number and its shadows disagree, that gap is where to look first. People, not the method, decide what to do about it.

**Why the name.** *Shadow*: every hidden quantity casts one. *Associative*: the method starts from associations between a hidden number and its shadows. Association is where it starts, not where it ends; Law 2 is what turns an association into evidence. *Prediction*: it predicts values nobody can see, whether now, in the past or later.

## 2. Scope

**Covers**

- Quantities that happen at scale and touch the physical world: emissions, energy, economic activity, pollution, land and sea.
- Numbers that are hidden, missing, late or possibly bent, where public data exists around them.

**Does not cover (v0.1)**

- Individual people. No personal data (R6).
- Events with no measurable warning in the data. The US Geological Survey says no scientist has ever predicted a major earthquake; this theory doesn't claim to either.
- Choosing what to do. The method estimates and flags; named people decide (R7).

## 3. Definitions

| Term | Meaning |
|---|---|
| Hidden quantity | A number that matters but can't be measured directly, or whose owner hides or bends it. Example: the coal a country actually burned. |
| Shadow | A different, measurable quantity that moves with the hidden one. Example: night-time light seen from space, for economic activity. The closest statistics term is the shadow variable: a variable that tracks a value that's missing because of what it is, but plays no part in it going missing ([Miao et al.](https://arxiv.org/abs/1509.02556)). |
| Angle | One source of evidence: an owner plus a method. A statistics office's table is one angle; a satellite operator's measurement is another. |
| Independent angles | Angles with different owners and different methods, so they can't share one mistake or one motive. Copies of the same source count once. |
| Official number | The figure a responsible body publishes for a hidden quantity. |
| Gap | The difference between an official number and what its shadows imply. |
| Cut-off | The size of gap at which someone acts. Always set by a named person (R7). |

## 4. Assumptions

Taken as given here, not tested.

- **A1.** Any source can be wrong, by accident or on purpose, official ones included.
- **A2.** Whether two angles are independent can be worked out, at least roughly, by tracing who owns them and how they measure.
- **A3.** For many hidden quantities, enough public data exists around them to look for shadows.

## 5. Laws

Each law gives its claim, its logic, what it predicts, and the result that would prove it wrong.

### L1. Everything casts a shadow

Anything that happens at scale leaves traces in things measured for other reasons.

```text
IF something happens at scale
THEN it leaves traces in quantities measured for other reasons
     (light, heat, gas, money, behaviour)
```

- **Predicts:** for a list of hidden quantities chosen in advance, a time-boxed search finds a shadow that passes the [shadow test](docs/shadow-test.md) for most of them.
- **False if:** the search finds a passing shadow for fewer of them than the threshold written down before it starts.
- **Weakest law:** one failed search doesn't disprove L1, because not finding a shadow isn't proof there is none. So L1 is judged by its hit rate across many searches, never by a single case.
- **Cases:** C06, C09, C12. **Test:** [T3](tests/T3-shadow-search.md).

### L2. One angle can lie; independent angles pin it down

```text
IF independent angles agree on a value
THEN trust in that value rises
IF they disagree
THEN the value stays unconfirmed, and the disagreement is itself a finding
```

- **Predicts:** in backtests on cases with known outcomes, values confirmed by two or more independent angles are right more often than values from one angle.
- **False if:** agreement between independent angles is no more accurate than a single angle.
- **Cases:** C01, C03, C04, C14. **Test:** [T2](tests/T2-city-air.md).

### L3. The gap is the signal

```text
IF an official number and its shadows disagree by more than the cut-off
THEN flag it, and look there first
```

- **Predicts:** flagged gaps come before later corrections, revisions or discoveries more often than chance.
- **False if:** flagged gaps predict later corrections no better than chance.
- **Cases:** C01, C02, C05, C06, C07, C08. **Test:** [T1](tests/T1-night-lights.md).

## 6. Working rules

Nine rules in three groups of three. Each was learned from a case in [cases/](cases/).

**Trusting sources**

- **R1. A source check is not a truth check.** A verified source proves who said something and when, not that it's true. (C05)
- **R2. Copies count once.** A hundred results from the same method are one angle. (C04, C14)
- **R3. Calibrate a shadow on independent, trusted sources, never on the source being checked.** A shadow calibrated on a liar inherits the lie. (C05, C06)

**Handling the unexpected**

- **R4. Park what can't be verified; never delete it.** Early warnings usually arrive unverified. (C16)
- **R5. Never drop an extreme automatically; check the reference too.** The reference can be the broken part. (C03)
- **R6. No personal data in v0.1.** Harmless data, joined, can expose people and places. (C10, C11)

**Acting**

- **R7. A named person sets every cut-off.** Act when the chance of the event is greater than the cost of acting divided by the loss if nobody acts: if evacuating costs €1M and an unwarned hit costs €100M, act above a 1% chance. Data supplies the chance; people supply the costs. (C15)
- **R8. Judge the method by how few things it puts in front of a person.** When the real thing is rare, most flags are false. (C12, C13)
- **R9. Every flag names who will act on it.** Detection without an owner changes nothing. (C02, C07, C08)

Checking a source and checking a value are separate jobs:

```text
source check:  WHO said it, WHEN      -> spoofed or not
cross-check:   IS IT TRUE             -> independent angles agree or not

both pass          -> trusted
source only        -> "official, unconfirmed"
cross-check only   -> "confirmed, source unknown"
neither            -> parked, never deleted (R4)
```

## 7. What the theory does not claim

- That data alone gives the best decision. Cheaper power versus cleaner air is a value choice.
- That a shadow is the thing itself. Every shadow has other causes; two failed shadows are kept on record (S12, S13).
- That one person can watch everything. That is the problem it's designed for.

## 8. Strongest objections

| Objection | Response so far | Status |
|---|---|---|
| **Scattered knowledge.** Hayek (1945): the knowledge that matters is spread across millions of people and mostly never written down. | Shadows recover some unwritten activity (electricity use reveals unreported work, S11), but not intentions or preferences. | Partly answered |
| **Shadows get gamed once known.** Volkswagen's cars detected the official test and behaved only during it (C04). | Independent angles (L2) and recalibration (R3) help, but any well-known shadow should be expected to degrade. | Open |
| **Screening everything floods people with false alarms.** When the real thing is rare, most flags are false (C12). | Owned cut-offs (R7) and judging the method by how few flags it raises (R8). | Open; tested by T2 |

## 9. Open questions

- How should independence be scored when two angles share part of their method?
- How many independent angles are enough: two, or three?
- How fast do shadows drift, and how often must each be re-checked?

## 10. Versions

See [CHANGELOG.md](CHANGELOG.md). Laws, rules, cases, shadows and tests keep their IDs across versions; a retired one is marked as retired, never reused.
