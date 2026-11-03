---
id: T3
title: Time-boxed shadow search
law: L1
status: planned
---

# T3. Time-boxed shadow search

**Tests:** L1, everything casts a shadow.

1. Before searching, write down a list of hidden quantities, a time box for each, and the hit-rate threshold.
2. For each quantity, search for shadows and score each one on the [shadow test](../docs/shadow-test.md).
3. Count the quantities with at least one shadow that passes.

- **Done when:** the hit rate meets or beats the threshold written down in step 1.
- **If it reads otherwise:** L1 weakens; record which kinds of quantity cast no usable shadow.

## Not decided yet

- The list, the time box and the threshold. They're fixed before the search starts, never after.
