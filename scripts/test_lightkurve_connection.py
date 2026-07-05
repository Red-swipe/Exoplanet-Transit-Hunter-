"""Test: network latency and full Lightkurve pipeline."""

import sys, time, subprocess, warnings
warnings.filterwarnings("ignore")

# Latency check
print("--- Ping to mast.stsci.edu ---")
sys.stdout.flush()
try:
    result = subprocess.run(["ping", "-n", "4", "mast.stsci.edu"], capture_output=True, text=True, timeout=30)
    for line in result.stdout.splitlines():
        if "ms" in line and ("Minimum" in line or "Average" in line or "Reply" in line):
            print(f"  {line.strip()}")
except Exception as e:
    print(f"  Ping failed: {e}")
sys.stdout.flush()

# Check for HTTP/2 vs HTTP/1.1 difference
print("\n--- Tracert (first 5 hops) ---")
sys.stdout.flush()
try:
    result = subprocess.run(["tracert", "-h", "5", "mast.stsci.edu"], capture_output=True, text=True, timeout=60)
    for line in result.stdout.splitlines():
        print(f"  {line}")
except Exception as e:
    print(f"  Tracert failed: {e}")
sys.stdout.flush()

# Now test lightkurve with generous timeout
import lightkurve as lk
import astroquery.mast

print("\n--- Lightkurve search_lightcurve(KIC 10000162) ---")
sys.stdout.flush()
# Extend every timeout we can find
from astroquery.mast import Mast, Observations
Mast.TIMEOUT = 300
Observations.TIMEOUT = 300

t0 = time.time()
result = lk.search_lightcurve("KIC 10000162", mission="Kepler")
elapsed = time.time() - t0
print(f"Completed in {elapsed:.1f}s")
print(f"Results: {0 if result is None else len(result)}")
if result is not None and len(result) > 0:
    print(f"Table:\n{result.table[:3]}")
sys.stdout.flush()
