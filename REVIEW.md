# Review guide

## Hard stops
- Stop if the demo uses real client data. The demo is fictional (Quillmere Plumbing).
- Stop on a ranking or AI-citation promise. Report measured results only.
- Hard stops of the HQ block apply: no secrets, no force-push, no push to main.

## Fragile files
- `audit.py`: NAP name matching broke twice. Commits 1ef92de and 4cf07eb fixed it after cross-model review. NAP compares declared structured sources only.
- `demo/site_before/`, `demo/site_after/`, `demo/out/`: `accept.py` expects 2/19 before and 19/19 after. A page edit changes the scores.
- `README.md`: it quotes the 2/19 and 19/19 scores. Update it with any score change.

## Tests that must pass
- `python accept.py`: ends with `ACCEPT: OK` (run). CI runs it (`checks.yml`).
- `python -m unittest tests.test_merge_gate -q`: OK (run).
- `tests/test_audit.py`: 39 tests, 1 failure on Windows (path separator, VERIFY.md). Run on Linux.
