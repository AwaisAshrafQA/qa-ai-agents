## Techniques (ISTQB CTFL v4.0.1, section 4.2) - name the technique and coverage item on every case
- Equivalence partitioning: split every input/output into non-overlapping valid and invalid partitions;
  one test per partition. With several parameters, at least "each choice" coverage (every partition once).
- Boundary value analysis (ordered partitions only). Use 3-value BVA: the boundary and both neighbours
  (e.g. limit 100 -> 99, 100, 101). It catches mistakes 2-value BVA misses (x <= 10 coded as x == 10).
- Decision tables: for business rules that combine conditions; one test per feasible column. Building the
  table exposes gaps and contradictions in the requirement: report them.
- State transition testing: for anything with a status/lifecycle. Cover all valid transitions (0-switch)
  at minimum; for critical flows also every invalid transition, one invalid transition per test.
- Combinatorial / pairwise: for many independent parameters (browsers x payment methods x roles).
  NIST data: most faults involve 1-2 interacting parameters, few more than 3; pairwise is not enough
  for critical paths.
- Use-case / scenario testing: main flow, every alternative and every exception flow, end to end.
- Error guessing: input, output, logic (missing case, wrong operator), computation (rounding, currency),
  interfaces (parameter mismatch), data (initialisation, types).

## Coverage expectations
- Every acceptance criterion and business rule traces to at least one test; every computed boundary probe
  appears in a boundary case.
- Negative tests: exactly ONE invalid input per test, otherwise one error masks another (ISTQB).
- Include non-functional cases the requirement implies: security (authorisation, injection), performance
  (response-time target), accessibility (WCAG 2.2 AA), reliability (retry, idempotency, double-submit).
- Integration: persistence, downstream documents/emails, payment or third-party callbacks, concurrency.

## Good test case (ISO/IEC/IEEE 29119-3 test case fields + practice)
- Unique id, objective/title, priority, traceability (requirement), preconditions, test data, steps,
  one observable expected result ("total is 164.00 AED", never "works correctly"), technique + coverage item.
- Deterministic and independent: own setup/cleanup, no reliance on other tests.

## Prioritisation (ISTQB CTFL v4.0.1, 5.1.5 / 5.2.1)
- Risk level = likelihood x impact: P1 for money, security, data loss, legal/compliance and core flows.
- Dependencies can override priority (a P1 test that needs a P2 setup runs after it).

## Edge-case data (Hendrickson et al.)
- Numbers: 0, negatives, decimals, very large (2^31, 2^32 +/- 1), separators (1,234.56 vs 1.234,56).
- Strings: empty, single space, leading/trailing spaces, 255/256/1024+ chars, unicode, emoji, RTL, injection.
- Dates: leap day, DST change, time zones, month/year end, expiry exactly now, different formats.
- Web: back, refresh, double-click submit, two tabs, session expiry, JavaScript/cookies off.

Sources: ISTQB CTFL v4.0.1 https://www.istqb.org/wp-content/uploads/2024/11/ISTQB_CTFL_Syllabus_v4.0.1.pdf · ISTQB BVA white paper
https://istqb.org/wp-content/uploads/2025/10/Boundary-Value-Analysis-white-paper.pdf · NIST combinatorial testing
https://csrc.nist.gov/projects/automated-combinatorial-testing-for-software/our-research-program · ISO/IEC/IEEE 29119-3:2021 ·
Hendrickson et al., Test Heuristics Cheat Sheet (2006) · ISO/IEC 25010:2023 · WCAG 2.2
