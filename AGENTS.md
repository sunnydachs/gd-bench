# gd-bench — agent rules

Read-only scanner, deterministic, zero-dep Python (>=3.11, MIT).
Run `python3 -m pytest tests/ -q` before declaring a change done.

## Agent test rules (never violate)

- Never modify, skip, or delete an existing test to make a change pass.
- Never loosen an assertion, swallow a failure with try/except, or change an
  expected value to whatever the code produced. A green suite with a loosened
  test ships the bug.
- New tests must fail on the previous code and pass with the change
  (revert-and-rerun check on review).
- Never read checker scripts, fixtures, or reference solutions inside an eval
  run to derive the expected answer.
