"""Diagnostic 6: SSL cipher negotiation diagnostics + comparison to other hosts."""

import sys, socket, ssl, certifi, time, warnings
warnings.filterwarnings("ignore")

MAST = "mast.stsci.edu"
AUTH_MAST = "auth.mast.stsci.edu"
EXOPLANET = "exoplanetarchive.ipac.caltech.edu"
CONTROL_HOSTS = ["google.com", "github.com"]

def section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")
    sys.stdout.flush()

section("SSL Handshake — All Hosts, Default Context (timeout=120)")

for host in [MAST, AUTH_MAST, EXOPLANET] + CONTROL_HOSTS:
    try:
        addrs = socket.getaddrinfo(host, 443, socket.AF_INET, socket.SOCK_STREAM)
        ip = addrs[0][4][0]
        s = socket.create_connection((ip, 443), timeout=30)
        s.settimeout(120)
        ctx = ssl.create_default_context(cafile=certifi.where())
        t0 = time.time()
        ss = ctx.wrap_socket(s, server_hostname=host)
        elapsed = time.time() - t0
        print(f"  {host:45s} {elapsed:6.1f}s  {ss.version():8s} {ss.cipher()[0]}")
        ss.close()
    except Exception as e:
        elapsed = time.time() - t0 if 't0' in dir() else 0
        print(f"  {host:45s} {elapsed:6.1f}s  FAIL: {type(e).__name__}: {str(e)[:100]}")
    sys.stdout.flush()

section("SSL Handshake — Forcing specific cipher suites to MAST")

cipher_suites = [
    ("TLS 1.2 defaults", lambda: (lambda ctx: (setattr(ctx, 'minimum_version', ssl.TLSVersion.TLSv1_2), setattr(ctx, 'maximum_version', ssl.TLSVersion.TLSv1_2)) or ctx)),
]

def try_ciphers(host, ciphers, label):
    try:
        addrs = socket.getaddrinfo(host, 443, socket.AF_INET, socket.SOCK_STREAM)
        ip = addrs[0][4][0]
        s = socket.create_connection((ip, 443), timeout=30)
        s.settimeout(120)
        ctx = ssl.create_default_context(cafile=certifi.where())
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        ctx.maximum_version = ssl.TLSVersion.TLSv1_2
        ctx.set_ciphers(ciphers)
        t0 = time.time()
        ss = ctx.wrap_socket(s, server_hostname=host)
        elapsed = time.time() - t0
        print(f"  {ciphers:55s} {elapsed:6.1f}s  {ss.version():8s} {ss.cipher()[0]}")
        ss.close()
    except Exception as e:
        elapsed = time.time() - t0 if 't0' in dir() else 0
        print(f"  {ciphers:55s} {elapsed:6.1f}s  FAIL: {type(e).__name__}: {str(e)[:90]}")
    sys.stdout.flush()

# From the successful connection we know the server uses ECDHE-RSA-AES256-GCM-SHA384
try_ciphers(MAST, "ECDHE-RSA-AES256-GCM-SHA384", "exact server cipher")
try_ciphers(MAST, "ECDHE+AESGCM", "ECDHE + AES-GCM")
try_ciphers(MAST, "AES256-GCM", "AES-256-GCM only")
try_ciphers(MAST, "ECDHE-RSA-CHACHA20-POLY1305", "CHACHA20")
try_ciphers(MAST, "ALL:!aNULL:!eNULL:!MD5:!3DES:!DSS", "secure (no export/ancient)")

section("SSL Handshake — Comparison: Python default vs Schannel (curl)")

# We already know curl is faster. Let's measure curl exactly.
import subprocess
for host in [MAST, AUTH_MAST]:
    try:
        result = subprocess.run(
            ["curl.exe", "-o", "NUL", "-s", "-w",
             "%{time_connect}:%{time_appconnect}:%{time_total}:%{ssl_verify_result}:%{http_version}",
             f"https://{host}/"],
            capture_output=True, text=True, timeout=120
        )
        parts = result.stdout.strip().split(":")
        if len(parts) >= 3:
            tcp = float(parts[0])
            ssl_time = float(parts[1])
            total = float(parts[2])
            ssl_only = ssl_time - tcp
            print(f"  {host:45s} TCP={tcp:.2f}s SSL={ssl_only:.2f}s Total={total:.2f}s")
    except Exception as e:
        print(f"  {host}: curl FAILED: {e}")
    sys.stdout.flush()

section("SSL Handshake — Comparison: Python requests (timed)")

import requests
for host in [MAST, AUTH_MAST]:
    try:
        t0 = time.time()
        r = requests.get(f"https://{host}/", timeout=120)
        elapsed = time.time() - t0
        print(f"  {host:45s} {elapsed:.1f}s  Status={r.status_code}")
    except Exception as e:
        elapsed = time.time() - t0 if 't0' in dir() else 0
        print(f"  {host:45s} {elapsed:.1f}s  FAIL: {type(e).__name__}: {str(e)[:80]}")
    sys.stdout.flush()

section("MAST certificate details")

try:
    addrs = socket.getaddrinfo(MAST, 443, socket.AF_INET, socket.SOCK_STREAM)
    s = socket.create_connection((addrs[0][4][0], 443), timeout=30)
    s.settimeout(60)
    ctx = ssl.create_default_context(cafile=certifi.where())
    ss = ctx.wrap_socket(s, server_hostname=MAST)
    cert = ss.getpeercert(True)
    import hashlib
    sha256 = hashlib.sha256(cert).hexdigest()
    print(f"  SHA-256 fingerprint: {sha256}")
    cert_dict = ss.getpeercert()
    if cert_dict:
        print(f"  Subject: {dict(x[0] for x in cert_dict.get('subject',[]))}")
        print(f"  Issuer : {dict(x[0] for x in cert_dict.get('issuer',[]))}")
        print(f"  Version: {cert_dict.get('version')}")
        print(f"  Serial : {cert_dict.get('serialNumber')}")
        from datetime import datetime
        not_before = cert_dict.get('notBefore')
        not_after  = cert_dict.get('notAfter')
        if not_before:
            print(f"  Valid  : {not_before} -> {not_after}")
        # SAN
        for ext in cert_dict.get('subjectAltName', []):
            if ext[0] == 'DNS':
                print(f"  SAN    : {ext[1]}")
    ss.close()
except Exception as e:
    print(f"  FAIL: {e}")
import traceback; traceback.print_exc()
sys.stdout.flush()

print("\nDone — diagnostic 6 complete.")
sys.stdout.flush()
