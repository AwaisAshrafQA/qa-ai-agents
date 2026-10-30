## Definition and scale
- A flaky test both passes and fails on the same code (Google). Google reported ~1.5% of test runs flaky
  and ~16% of tests showing some flakiness; large/end-to-end tests (e.g. WebDriver) were far flakier than
  small ones, and test size predicted flakiness better than the tool.

## Root-cause categories (Luo et al. 2014; Eck et al. 2019; Gruber et al. 2022 review)
- async_wait: the test doesn't wait properly for an async result (fixed sleeps, missing waitFor). The most
  common cause in Luo et al. and at Microsoft; the usual fix is waiting for a condition instead of sleeping.
- concurrency: races, deadlocks, atomicity violations between threads/processes.
- test_order_dependency: passes or fails depending on which tests ran before (shared static state, DB rows,
  files). Lam et al. (iDFlakies) found about half of the flaky tests in their dataset were order-dependent.
- resource_leak, io: unclosed files, connections or browser contexts; file-system assumptions.
- network: remote or local network calls, third-party sandboxes.
- time: dates, time zones, DST, midnight, clocks, timeouts too tight. Eck et al. also found test case
  and suite timeouts and "too restrictive range" assertions.
- randomness, floating_point, unordered_collection: unseeded random data, float equality, assuming
  set/map/JSON key order.
- platform_dependency: OS, browser, CI agent or environment-specific behaviour.
- shared_test_data / external_dependency: data or services outside the test's control.

## Detection
- Rerun at the same commit: pass and fail on the same SHA = flaky.
- Reverse / random order and isolated runs: fails only in some orders = order-dependent (find the polluter).
- Vary seed, clock, time zone, locale and platform; run under load or with injected delay for async/concurrency.
- Compare runtime with the timeout: close to the limit = timeout flakiness.

## Metrics
- Flip rate = pass<->fail transitions / (runs - 1) (Kowalczyk et al., Apple). It measures instability
  over time, unlike the fail rate. Apple ranked tests by flip rate over windows with a moving average.
- A high fail rate with a low flip rate is a consistently failing (broken) test: treat it as a defect, not flakiness.
- Re-measure after a fix: Microsoft found some claimed fixes did not reduce the failure rate.

## Handling
- Quarantine only with an owner and a fix-by date; a quarantined test still runs and reports, it just
  doesn't block. Never delete or retry-until-green without tracking.
- Fix order: highest flip rate x business-critical path first.

Sources: Luo et al., "An Empirical Analysis of Flaky Tests", FSE 2014 · Eck et al., "Understanding Flaky Tests:
The Developer's Perspective", FSE 2019 https://arxiv.org/abs/1907.01466 · Parry et al., "A Survey of Flaky Tests",
TOSEM 2021 · Gruber et al. 2022 https://arxiv.org/abs/2212.00908 · Lam et al., "iDFlakies", ICST 2019 · Lam et al.,
"A Study on the Lifecycle of Flaky Tests", ICSE 2020 · Kowalczyk et al., "Modeling and Ranking Flaky Tests at Apple",
ICSE-SEIP 2020 · Google Testing Blog https://testing.googleblog.com/2016/05/flaky-tests-at-google-and-how-we.html and
https://testing.googleblog.com/2017/04/where-do-our-flaky-tests-come-from.html
