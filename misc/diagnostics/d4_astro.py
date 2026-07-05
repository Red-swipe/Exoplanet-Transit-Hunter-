"""Diagnostic 4: astroquery & lightkurve internals — catching exact failures."""

import sys, time, warnings, traceback, logging
warnings.filterwarnings("ignore")

BASE = "https://mast.stsci.edu"

def section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")
    sys.stdout.flush()

section("astroquery.mast.Mast.service_request (simple)")

try:
    from astroquery.mast import Mast
    Mast.TIMEOUT = 300

    t0 = time.time()
    resp = Mast.service_request(
        "Mast.Caom.Cone",
        {"position": None, "database": "Kepler", "table": "observations"},
        format="json"
    )
    elapsed = time.time() - t0
    print(f"  OK  ({elapsed:.1f}s)  type={type(resp).__name__}")
    if hasattr(resp, '__len__'):
        print(f"  Rows: {len(resp)}")
    sys.stdout.flush()
except Exception as e:
    elapsed = time.time() - t0 if 't0' in dir() else 0
    print(f"  FAIL ({elapsed:.1f}s) {type(e).__name__}: {e}")
    traceback.print_exc()
    sys.stdout.flush()

section("astroquery.mast.Observations.query_criteria (target=KIC 10000162)")

try:
    from astroquery.mast import Observations
    Observations.TIMEOUT = 300

    t0 = time.time()
    obs = Observations.query_criteria(
        obs_collection="Kepler",
        target_name="KIC 10000162",
        radius="0.001 deg",
    )
    elapsed = time.time() - t0
    print(f"  OK  ({elapsed:.1f}s)")
    if obs is not None:
        print(f"  Rows: {len(obs)}")
    else:
        print(f"  Returned: None")
    sys.stdout.flush()
except Exception as e:
    elapsed = time.time() - t0 if 't0' in dir() else 0
    print(f"  FAIL ({elapsed:.1f}s) {type(e).__name__}: {e}")
    traceback.print_exc()
    sys.stdout.flush()

section("astroquery.mast.Observations.query_criteria (blanket, no target)")

try:
    t0 = time.time()
    obs2 = Observations.query_criteria(
        obs_collection="Kepler",
        radius="0.001 deg",
        limit=3,
    )
    elapsed = time.time() - t0
    print(f"  OK  ({elapsed:.1f}s)")
    if obs2 is not None:
        print(f"  Rows: {len(obs2)}")
        print(f"  Columns: {obs2.colnames}")
        if len(obs2) > 0:
            print(f"  First target_name: {obs2['target_name'][0]}")
    else:
        print(f"  Returned: None")
    sys.stdout.flush()
except Exception as e:
    elapsed = time.time() - t0 if 't0' in dir() else 0
    print(f"  FAIL ({elapsed:.1f}s) {type(e).__name__}: {e}")
    traceback.print_exc()
    sys.stdout.flush()

section("lightkurve.search_lightcurve (KIC 10000162)")

try:
    import lightkurve as lk

    t0 = time.time()
    result = lk.search_lightcurve("KIC 10000162", mission="Kepler")
    elapsed = time.time() - t0
    print(f"  OK  ({elapsed:.1f}s)")
    if result is not None:
        print(f"  Results: {len(result)}")
        if len(result) > 0:
            print(f"  Table:\n{result.table[:2]}")
    else:
        print(f"  Returned: None")
    sys.stdout.flush()
except Exception as e:
    elapsed = time.time() - t0 if 't0' in dir() else 0
    print(f"  FAIL ({elapsed:.1f}s) {type(e).__name__}: {e}")
    traceback.print_exc()
    sys.stdout.flush()

section("lightkurve.search_lightcurve (blanket, 3 results)")

try:
    import lightkurve as lk

    t0 = time.time()
    result2 = lk.search_lightcurve("KIC 10000162", mission="Kepler")
    elapsed = time.time() - t0
    print(f"  OK  ({elapsed:.1f}s)")
    if result2 is not None:
        print(f"  Results: {len(result2)}")
        if len(result2) > 0:
            print(f"  Table:\n{result2.table[:2]}")
    else:
        print(f"  Returned: None")
    sys.stdout.flush()
except Exception as e:
    elapsed = time.time() - t0 if 't0' in dir() else 0
    print(f"  FAIL ({elapsed:.1f}s) {type(e).__name__}: {e}")
    traceback.print_exc()
    sys.stdout.flush()

print("\nDone — diagnostic 4 complete.")
sys.stdout.flush()
