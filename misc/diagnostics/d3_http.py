"""Diagnostic 3: Python HTTP stack — requests, urllib, urllib3 (raw), connection reuse."""

import sys, time, warnings, ssl, socket
warnings.filterwarnings("ignore")

BASE = "https://mast.stsci.edu"

def section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")
    sys.stdout.flush()

section("requests.get() — simple GET")

import requests
try:
    t0 = time.time()
    r = requests.get(f"{BASE}/portal/Mashup/Mashup.asmx", timeout=120)
    elapsed = time.time() - t0
    print(f"  Status: {r.status_code}  ({elapsed:.1f}s)  len={len(r.text)}")
except Exception as e:
    elapsed = time.time() - t0 if 't0' in dir() else 0
    print(f"  FAIL ({elapsed:.1f}s) {type(e).__name__}: {str(e)[:150]}")
sys.stdout.flush()

section("requests.get() — POST JSON (columnsconfig)")

headers = {"Content-Type": "application/json"}
payload = '{"columns":"*","filters":{}}'
try:
    t0 = time.time()
    r = requests.post(f"{BASE}/portal/Mashup/Mashup.asmx/columnsconfig",
                      data=payload, headers=headers, timeout=120)
    elapsed = time.time() - t0
    print(f"  Status: {r.status_code}  ({elapsed:.1f}s)  len={len(r.text)}")
except Exception as e:
    elapsed = time.time() - t0 if 't0' in dir() else 0
    print(f"  FAIL ({elapsed:.1f}s) {type(e).__name__}: {str(e)[:150]}")
sys.stdout.flush()

section("requests.get() — session reuse (2 sequential calls)")

try:
    sess = requests.Session()
    t0 = time.time()
    r1 = sess.post(f"{BASE}/portal/Mashup/Mashup.asmx/columnsconfig",
                   data=payload, headers=headers, timeout=120)
    t1 = time.time()
    r2 = sess.post(f"{BASE}/portal/Mashup/Mashup.asmx/columnsconfig",
                   data=payload, headers=headers, timeout=120)
    t2 = time.time()
    print(f"  Request 1: {r1.status_code} ({t1-t0:.1f}s)")
    print(f"  Request 2: {r2.status_code} ({t2-t1:.1f}s)  (should be fast if session reuse works)")
except Exception as e:
    print(f"  FAIL: {type(e).__name__}: {str(e)[:150]}")
sys.stdout.flush()

section("requests.get() — verify=False (skip cert validation)")

try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    t0 = time.time()
    r = requests.post(f"{BASE}/portal/Mashup/Mashup.asmx/columnsconfig",
                      data=payload, headers=headers, timeout=120, verify=False)
    elapsed = time.time() - t0
    print(f"  Status: {r.status_code}  ({elapsed:.1f}s)  len={len(r.text)}")
except Exception as e:
    elapsed = time.time() - t0 if 't0' in dir() else 0
    print(f"  FAIL ({elapsed:.1f}s) {type(e).__name__}: {str(e)[:150]}")
sys.stdout.flush()

section("urllib.request — raw")

import urllib.request
try:
    req = urllib.request.Request(f"{BASE}/portal/Mashup/Mashup.asmx/columnsconfig",
                                  data=b'{"columns":"*","filters":{}}',
                                  headers=headers, method="POST")
    t0 = time.time()
    resp = urllib.request.urlopen(req, timeout=120)
    elapsed = time.time() - t0
    body = resp.read()
    print(f"  Status: {resp.status}  ({elapsed:.1f}s)  len={len(body)}")
except Exception as e:
    elapsed = time.time() - t0 if 't0' in dir() else 0
    print(f"  FAIL ({elapsed:.1f}s) {type(e).__name__}: {str(e)[:150]}")
sys.stdout.flush()

section("urllib3 (pool manager, raw)")

import urllib3
urllib3.disable_warnings()
try:
    http = urllib3.PoolManager(timeout=urllib3.Timeout(total=120))
    t0 = time.time()
    r = http.request("POST", f"{BASE}/portal/Mashup/Mashup.asmx/columnsconfig",
                     body=payload, headers=headers)
    elapsed = time.time() - t0
    print(f"  Status: {r.status}  ({elapsed:.1f}s)  len={len(r.data)}")
except Exception as e:
    elapsed = time.time() - t0 if 't0' in dir() else 0
    print(f"  FAIL ({elapsed:.1f}s) {type(e).__name__}: {str(e)[:150]}")
sys.stdout.flush()

section("urllib3 — HTTPS connection pool reuse (3 calls)")

try:
    http = urllib3.HTTPSConnectionPool("mast.stsci.edu", port=443,
                                        maxsize=10, timeout=120)
    times = []
    for i in range(3):
        t0 = time.time()
        r = http.request("POST", "/portal/Mashup/Mashup.asmx/columnsconfig",
                         body=payload, headers=headers)
        times.append(time.time() - t0)
        print(f"  Call {i+1}: {r.status} ({times[-1]:.1f}s)")
    print(f"  Speedup: {times[0]/max(times[1],0.001):.1f}x after connection reuse")
except Exception as e:
    print(f"  FAIL: {type(e).__name__}: {str(e)[:150]}")
sys.stdout.flush()

section("requests — Exoplanet Archive (alternative endpoint)")

try:
    t0 = time.time()
    r = requests.get("https://exoplanetarchive.ipac.caltech.edu", timeout=30)
    elapsed = time.time() - t0
    print(f"  Status: {r.status_code}  ({elapsed:.1f}s)")
except Exception as e:
    elapsed = time.time() - t0 if 't0' in dir() else 0
    print(f"  FAIL ({elapsed:.1f}s) {type(e).__name__}: {str(e)[:150]}")
sys.stdout.flush()

print("\nDone — diagnostic 3 complete.")
sys.stdout.flush()
