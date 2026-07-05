"""Diagnostic 1: Python environment, SSL, certifi, OpenSSL details."""

import sys, platform, ssl, certifi, os, textwrap

def section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")
    sys.stdout.flush()

section("Python & Platform")

print(f"Python version : {sys.version}")
print(f"Platform       : {platform.platform()}")
print(f"Windows version: {platform.win32_ver()}")
print(f"Architecture   : {platform.machine()}")
print(f"Processor      : {platform.processor()}")
print(f"Hostname       : {platform.node()}")
sys.stdout.flush()

section("OpenSSL")

try:
    print(f"OpenSSL version: {ssl.OPENSSL_VERSION}")
    print(f"OpenSSL built   : {ssl.OPENSSL_VERSION_INFO}")
    print(f"Default cipher list: {ssl._DEFAULT_CIPHERS}")
except AttributeError:
    try:
        ctx = ssl.create_default_context()
        print(f"OpenSSL version: {ssl.OPENSSL_VERSION}")
        print(f"Default ciphers: {ctx.get_ciphers()[:5]}")
    except Exception as e:
        print(f"Could not get cipher list: {e}")
sys.stdout.flush()

section("Certifi")

print(f"certifi version : {certifi.__version__}")
print(f"certifi path    : {certifi.where()}")
cert_size = os.path.getsize(certifi.where())
print(f"certifi size    : {cert_size:,} bytes")
with open(certifi.where(), "r") as f:
    lines = f.readlines()
ca_count = sum(1 for l in lines if l.startswith("-----BEGIN CERTIFICATE-----"))
print(f"certifi certs   : {ca_count}")
sys.stdout.flush()

section("Default SSL Context")

ctx = ssl.create_default_context()
print(f"Protocol            : {ctx.protocol}")
print(f"Verify mode         : {ctx.verify_mode}")
print(f"Check hostname      : {ctx.check_hostname}")
print(f"Minimum TLS version : {ssl._DEFAULT_MINIMUM_VERSION if hasattr(ssl, '_DEFAULT_MINIMUM_VERSION') else ctx.minimum_version}")
print(f"Maximum TLS version : {ssl._DEFAULT_MAXIMUM_VERSION if hasattr(ssl, '_DEFAULT_MAXIMUM_VERSION') else ctx.maximum_version}")
sys.stdout.flush()

section("Available TLS Versions")

for name in ["TLSv1_2", "TLSv1_3"]:
    try:
        v = getattr(ssl.TLSVersion, name, None)
        if v:
            print(f"  {name} available")
    except:
        pass
sys.stdout.flush()

section("Windows Certificate Store (via Python)")

try:
    ctx.load_default_certs()
    count = len(ctx.get_ca_certs())
    print(f"System certs loaded: {count}")
    # Show first few
    for cert in ctx.get_ca_certs()[:3]:
        subj = dict(cert.get("subject", []))
        cn = [v for k, v in subj if k == (2, 5, 4, 3)] or ["unknown"]
        print(f"  - {cn[0]}")
except Exception as e:
    print(f"Could not load system certs: {e}")
sys.stdout.flush()

section("Environment Variables (relevant)")

proxy_vars = ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy",
              "NO_PROXY", "no_proxy", "SSL_CERT_FILE", "SSL_CERT_DIR",
              "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE", "WEBSOCKET_CLIENT_CA_BUNDLE"]
for var in proxy_vars:
    val = os.environ.get(var, "<NOT SET>")
    if val != "<NOT SET>":
        print(f"  {var} = {val!r}")
    else:
        print(f"  {var} = {val}")
sys.stdout.flush()

section("Python path & site-packages")

import importlib, subprocess

print(f"sys.executable: {sys.executable}")
print(f"sys.prefix    : {sys.prefix}")
print("")
for mod in ["requests", "urllib3", "certifi", "cryptography", "astropy", "astroquery", "lightkurve"]:
    try:
        m = importlib.import_module(mod)
        ver = getattr(m, "__version__", "unknown")
        loc = getattr(m, "__file__", "unknown")
        print(f"  {mod:20s} v{ver:<12s} {loc}")
    except ImportError:
        print(f"  {mod:20s} NOT INSTALLED")
sys.stdout.flush()

print("\nDone — diagnostic 1 complete.")
sys.stdout.flush()
