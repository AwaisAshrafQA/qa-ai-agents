<!-- Generated from qa_agents/knowledge/requirement-review.md by scripts/sync_skill_references.py. Do not edit here. -->

## Quality of each requirement (ISO/IEC/IEEE 29148:2018)
- Necessary, appropriate, unambiguous, complete, singular (one requirement per statement; "and"/"or"
  often hides two), feasible, verifiable, correct, conforming.
- The set must be complete, consistent (no contradictions), feasible, comprehensible and able to be validated.

## User stories: INVEST (Bill Wake, 2003; ISTQB CTFL v4.0.1 4.5.1)
- Independent, Negotiable, Valuable ("so that" states the benefit), Estimable, Small, Testable.
- If a stakeholder cannot say how to test a story, the story is unclear (ISTQB).

## Acceptance criteria (ISTQB CTFL v4.0.1 4.5.2; Cucumber/Gherkin guidance)
- Must define scope, cover positive AND negative scenarios, and be well-defined and unambiguous.
- Scenario style (Given/When/Then) or rule style (verification list, input -> output table).
- Given = known state, no user action. When = one event. Then = an observable outcome (UI, message,
  API response), not hidden internals. 3-5 steps; declarative, not click-by-click.
- Concrete examples (actual values, roles, amounts), exact error messages, every business rule covered.

## Ambiguity indicators
- NASA ARM weak phrases: adequate, as a minimum, as applicable, easy, as appropriate, be able to, be capable,
  but not limited to, capability of/to, effective, if practical, normal, provide for, timely, TBD.
- Options (unclear obligation): can, may, optionally. "should" is weaker than "shall/must".
- Requirements smells (Femmer et al.): subjective language (user friendly, easy to use, fast, intuitive),
  loopholes (as far as possible, if possible, where feasible), superlatives (best, highest), comparatives
  (faster, better), vague pronouns (it, this, they), open-ended lists (etc., and so on), negatives.

## Edge cases to probe (Hendrickson et al. Test Heuristics Cheat Sheet; Bach HTSM SFDIPOT)
- Count: 0, 1, many, max. Goldilocks: too small, too big, just right. Position: first, middle, last.
- CRUD on every entity; Follow the data (create -> search -> report -> export -> import -> update).
- Interruptions: timeout, cancel, back/refresh/double-submit, network loss, session expiry, app killed.
- Multi-user: same record edited twice, same account in two sessions, concurrent purchases.
- Selection/permissions: none, some, all roles; logged out; another user's data.
- Time: time zones, DST, midnight, month end, leap day, expiry exactly now; holidays.
- Data: blank, spaces, very long, unicode/RTL, special characters, duplicates, invalid formats, currency/rounding.
- Idempotency (RFC 9110): retries and duplicate submissions must not double-charge or double-create.
- States: every status transition, including invalid ones (cancel after shipped).

## Non-functional requirements (ISO/IEC 25010:2023 product quality)
- Functional suitability, performance efficiency, compatibility, interaction capability (usability,
  inclusivity), reliability, security, maintainability, flexibility (portability, scalability), safety.
- Accessibility baseline: WCAG 2.2 Level AA (incl. new 2.4.11 focus not obscured, 2.5.8 target size,
  3.3.7 redundant entry, 3.3.8 accessible authentication).
- A story with UI, money, personal data or external calls without any NFR (response time, security,
  audit, accessibility, error handling) is incomplete.

Sources: ISO/IEC/IEEE 29148:2018 https://www.iso.org/standard/72089.html · INVEST https://xp123.com/invest-in-good-stories-and-smart-tasks/ ·
ISTQB CTFL v4.0.1 https://www.istqb.org/wp-content/uploads/2024/11/ISTQB_CTFL_Syllabus_v4.0.1.pdf · NASA ARM (Wilson, 1997)
https://www.csc.kth.se/utbildning/kth/kurser/DD1363/NASARequirements.html · Femmer et al., "Rapid quality assurance with
Requirements Smells", JSS 2017 https://arxiv.org/pdf/1611.08847 · Cucumber https://cucumber.io/docs/bdd/better-gherkin/ ·
Hendrickson et al., Test Heuristics Cheat Sheet (2006) · Bach, Heuristic Test Strategy Model https://www.satisfice.com/download/heuristic-test-strategy-model ·
ISO/IEC 25010:2023 https://iso25000.com/index.php/en/iso-25000-standards/iso-25010 · WCAG 2.2 https://www.w3.org/WAI/standards-guidelines/wcag/new-in-22/
