---
name: qa-test-case-generation
description: Design positive, negative, boundary and integration test cases from requirements or user stories, with concrete test data and expected results. Use when the user asks for test cases, test scenarios or a test suite for a feature.
---

# Test Case Generation

## 1. Get the facts

Save the requirement to a Markdown file if it was pasted, then run:

```bash
qa-agents facts test-case-generation <requirement.md>
```

If `qa-agents` is missing, install it: `pip install git+https://github.com/AwaisAshrafQA/qa-ai-agents`.

`facts.numeric_limits` lists every limit found in the text with its probe values (below, at and above). These come from code: every probe value needs a boundary case.

## 2. Analyse

Follow `instructions`. If the project has existing tests, read a few so the cases match its domain language and priorities.

## 3. Report

A table of cases (id, title, type, priority, preconditions, steps, test data, expected result, requirement), then coverage notes and automation candidates. Finish with the count of cases by type.

## 4. Offer next steps

- Export the cases as CSV for TestRail, Xray or Zephyr.
- Write automated tests for the automation candidates in the project's own framework (Playwright, Cypress, REST Assured, pytest...), then run them.
