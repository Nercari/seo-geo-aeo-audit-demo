# VERIFY

Merge evidence for seo-geo-aeo-audit-demo. Paste the real output of these commands in the PR body. When behavior changes, update this file in the same PR.

## Essential check

The acceptance script CI runs. tests/test_audit.py has one Windows path-separator failure, so it stays local.

```
python3 accept.py
python -m unittest tests.test_merge_gate -q
```
