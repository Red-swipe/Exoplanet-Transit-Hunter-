"""Diagnostic 2: Network layer — DNS, ping, connectivity, TCP sockets, route."""

import sys, socket, subprocess, time, warnings
warnings.filterwarnings("ignore")

HOSTS = [
    "mast.stsci.edu",
    "auth.mast.stsci.edu",
    "archive.stsci.edu",
    "exoplanetarchive.ipac.caltech.edu",
    "github.com",
]

def section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")
    sys.stdout.flush()

section("DNS Resolution")

for host in HOSTS:
    for family, label in [(socket.AF_INET, "IPv4"), (socket.AF_INET6, "IPv6")]:
        try:
            addrs = socket.getaddrinfo(host, 443, family, socket.SOCK_STREAM)
            for a in addrs[:2]:
                ip = a[4][0]
                print(f"  {label:4s} {host:40s} -> {ip}")
        except socket.gaierror as e:
            print(f"  {label:4s} {host:40s} -> FAIL: {e}")
    sys.stdout.flush()

section("TCP Socket Connect (port 443)")

for host in HOSTS:
    for family, label in [(socket.AF_INET, "IPv4")]:
        try:
            addrs = socket.getaddrinfo(host, 443, family, socket.SOCK_STREAM)
            if not addrs:
                print(f"  {host:40s} no address for {label}")
                continue
            ip = addrs[0][4][0]
            t0 = time.time()
            s = socket.create_connection((ip, 443), timeout=30)
            elapsed = time.time() - t0
            print(f"  {host:40s} {label:4s} OK  ({elapsed:.1f}s) sock={s.family}")
            s.close()
        except Exception as e:
            elapsed = time.time() - t0 if 't0' in dir() else 0
            print(f"  {host:40s} {label:4s} FAIL ({elapsed:.1f}s) {type(e).__name__}: {e}")
    sys.stdout.flush()

section("SSL Handshake (timeout=120s)")

import ssl, certifi

for host in HOSTS:
    try:
        addrs = socket.getaddrinfo(host, 443, socket.AF_INET, socket.SOCK_STREAM)
        if not addrs:
            continue
        ip = addrs[0][4][0]
        s = socket.create_connection((ip, 443), timeout=120)
        s.settimeout(120)
        ctx = ssl.create_default_context(cafile=certifi.where())
        t0 = time.time()
        ss = ctx.wrap_socket(s, server_hostname=host)
        elapsed = time.time() - t0
        cert = ss.getpeercert()
        issuer = dict(x[0] for x in cert.get("issuer", []))
        subject = dict(x[0] for x in cert.get("subject", []))
        print(f"  {host:40s} OK ({elapsed:.1f}s) TLS={ss.version()} cipher={ss.cipher()[0]}")
        print(f"  {'':40s} issuer={issuer.get('organizationName','?')} subject={subject.get('commonName','?')}")
        ss.close()
    except Exception as e:
        elapsed = time.time() - t0 if 't0' in dir() else 0
        print(f"  {host:40s} FAIL ({elapsed:.1f}s) {type(e).__name__}: {str(e)[:120]}")
    sys.stdout.flush()

section("Ping (4 packets each)")

for host in HOSTS[:3]:
    try:
        result = subprocess.run(
            ["ping", "-n", "4", host],
            capture_output=True, text=True, timeout=30
        )
        for line in result.stdout.splitlines():
            if "ms" in line or "TTL" in line or "Lost" in line or "sent" in line:
                print(f"  {host}: {line.strip()}")
    except subprocess.TimeoutExpired:
        print(f"  {host}: ping timed out")
    except FileNotFoundError:
        print(f"  {host}: ping not available")
    sys.stdout.flush()

section("Tracert (max 10 hops)")

for host in HOSTS[:2]:
    try:
        result = subprocess.run(
            ["tracert", "-h", "10", host],
            capture_output=True, text=True, timeout=60
        )
        for line in result.stdout.splitlines():
            if line.strip():
                print(f"  {line}")
    except Exception as e:
        print(f"  {host}: tracert error: {e}")
    sys.stdout.flush()

print("\nDone — diagnostic 2 complete.")
sys.stdout.flush()
