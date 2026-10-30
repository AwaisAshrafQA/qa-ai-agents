---
name: qa-requirement-review
description: Review user stories or requirements for missing acceptance criteria, edge cases, ambiguous wording and contradictions before development starts. Use when the user shares stories, a PRD or a ticket and asks whether it is ready, testable or complete.
---

# Requirement Review

## 1. Get the facts

Save the stories to a Markdown file if they were pasted (one `#` heading per story), then run:

```bash
qa-agents facts requirement-review <stories.md>
```

If `qa-agents` is missing, install it: `pip install git+https://github.com/AwaisAshrafQA/qa-ai-agents`.

The JSON contains `instructions`, `output_fields` and `facts` (acceptance-criteria count, Given/When/Then lines and vague terms per story). The facts come from code: use them exactly.

## 2. Analyse

Follow `instructions`. Read every story yourself; use the vague terms as leads, not as the whole review.

## 3. Report

One section per field in `output_fields`: a readiness verdict per story, issues as a table (story, category, severity, finding, question for the product owner), then suggested acceptance criteria in Given/When/Then form.

## 4. Offer next steps

- Rewrite each story with the suggested acceptance criteria, ready to paste into the ticket.
- Turn the questions into a refinement-meeting agenda.
