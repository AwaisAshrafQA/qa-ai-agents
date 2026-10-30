## What developers need (Bettenburg, Zimmermann et al., "What Makes a Good Bug Report?", FSE 2008)
- Most helpful: steps to reproduce, stack traces and test cases. These are also what reporters most often leave out.
- Most harmful: inaccurate steps to reproduce and incomplete information. Verify every step against the evidence.

## Required content (ISO/IEC/IEEE 29119-3 incident report; ISTQB CTFL v4.0 defect report)
- Unique, specific title; summary; date and author; test object, build/version and environment
  (browser, OS, device, app version, backend env); context (test case, feature, phase).
- Preconditions and test data; numbered, minimal, deterministic steps; expected vs actual result with
  exact values, messages and status codes; reproducibility (e.g. 3/3, intermittent 1/5).
- Evidence: logs with timestamps and request ids, screenshots/recordings, API request and response.
- Severity and priority, each justified; risk/impact (users, revenue, data, compliance); status; references
  (story, test case, related defects).

## Severity vs priority (ISTQB glossary)
- Severity = degree of impact on the development or operation of the system (set from the technical side).
- Priority = business importance / urgency of fixing (set by product or triage).
- Common severity scale: critical = crash, data loss or corruption, security breach or core flow blocked
  with no workaround; major = major function broken, hard workaround; minor = partial loss, easy workaround;
  trivial = cosmetic.
- Money miscalculation, wrong data stored, privacy exposure and security issues are never trivial.

## Writing rules
- One defect per report. Title format: [Component] What fails, under which condition.
- State facts, not blame; mark the suspected root cause as suspected.
- Mask secrets and personal data in logs and screenshots before filing.
- Put unknowns under open questions instead of guessing (build, frequency, affected users).

Sources: Bettenburg et al., FSE 2008 https://www.st.cs.uni-saarland.de/softevo/bugreports.php · ISO/IEC/IEEE 29119-3:2021,
clause 8.11 (Incident Report) · ISTQB CTFL v4.0 syllabus, section 5.5
https://istqb.org/certifications/certified-tester-foundation-level-ctfl-v4-0 · ISTQB Glossary (severity, priority)
