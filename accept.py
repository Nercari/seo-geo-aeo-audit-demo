import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import audit

HERE = Path(__file__).parent
MIN_BEFORE_FAILS = 8

rb, pb, tb, _ = audit.run(HERE / "site_before")
ra, pa, ta, _ = audit.run(HERE / "site_after")
fails_before = [r[0] for r in rb if not r[2]]
fails_after = [r[0] for r in ra if not r[2]]
print(f"site_before: {pb}/{tb} checks pass, {len(fails_before)} distinct failing checks")
print("  failing: " + ", ".join(fails_before))
print(f"site_after:  {pa}/{ta} checks pass, {len(fails_after)} failing")
ok = True
if len(fails_before) < MIN_BEFORE_FAILS:
    print(f"FAIL: site_before has only {len(fails_before)} failing checks, need >= {MIN_BEFORE_FAILS}")
    ok = False
if fails_after:
    print("FAIL: site_after still fails: " + ", ".join(fails_after))
    ok = False
print("ACCEPT: OK" if ok else "ACCEPT: FAILED")
sys.exit(0 if ok else 1)
