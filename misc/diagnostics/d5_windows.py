"""Diagnostic 5: Windows-side investigation — registry, proxy, firewall, tests."""

import sys, subprocess, os, winreg, platform, ctypes, time

def section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")
    sys.stdout.flush()

def run(cmd, timeout=30):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "<TIMEOUT>", "", -1
    except FileNotFoundError:
        return "<NOT FOUND>", "", -1
    except Exception as e:
        return f"<{e}>", "", -1

section("Windows Proxy Settings — Registry (INTERNET_SETTINGS)")

try:
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                         r"Software\Microsoft\Windows\CurrentVersion\Internet Settings")
    for i in range(10):
        try:
            name, val, typ = winreg.EnumValue(key, i)
            if name in ("ProxyEnable", "ProxyServer", "ProxyOverride", "AutoConfigURL",
                        "MigrateProxy", "AutoDetect"):
                print(f"  {name} = {val}")
        except WindowsError:
            break
    winreg.CloseKey(key)
except Exception as e:
    print(f"  Cannot read registry: {e}")
sys.stdout.flush()

section("Windows Proxy — netsh winhttp")

out, err, rc = run(["netsh", "winhttp", "show", "proxy"])
for line in out.splitlines():
    line = line.strip()
    if line:
        print(f"  {line}")
sys.stdout.flush()

section("Windows Firewall — status")

out, err, rc = run(["netsh", "advfirewall", "show", "allprofiles"])
for line in out.splitlines():
    l = line.strip()
    if "State" in l or "Profile" in l:
        print(f"  {l}")
sys.stdout.flush()

section("Windows Defender / Antivirus")

try:
    import wmi
    c = wmi.WMI()
    for product in c.Win32_Product():
        if "defender" in str(product.Name).lower() or "antivirus" in str(product.Name).lower() or "security" in str(product.Name).lower():
            print(f"  {product.Name} v{product.Version}")
except ImportError:
    # fallback via WMIC
    out, err, rc = run(
        ['cmd', '/c', 'wmic', '/namespace:\\\\root\\SecurityCenter2', 'path', 'AntivirusProduct', 'get', 'displayName']
    )
    for line in out.splitlines():
        line = line.strip()
        if line and line != "displayName":
            print(f"  Antivirus: {line}")
    if not out.strip():
        out, err, rc = run(
            ['powershell', '-Command',
             'Get-MpComputerStatus | Select-Object -Property AntivirusEnabled,RealTimeProtectionEnabled | Format-List']
        )
        for line in out.splitlines():
            line = line.strip()
            if line:
                print(f"  {line}")
sys.stdout.flush()

section("System-wide HTTPS test — PowerShell Invoke-WebRequest")

ps_script = '''
try {
    $r = Invoke-WebRequest -Uri "https://mast.stsci.edu/portal/Mashup/Mashup.asmx/columnsconfig" `
        -Method POST `
        -Body '{"columns":"*","filters":{}}' `
        -ContentType "application/json" `
        -UseBasicParsing `
        -TimeoutSec 120
    Write-Output "Status: $($r.StatusCode)"
    Write-Output "Elapsed: not measured"
} catch {
    Write-Output "ERROR: $($_.Exception.Message)"
}
'''
out, err, rc = run(["powershell", "-Command", ps_script], timeout=150)
for line in out.splitlines():
    line = line.strip()
    if line:
        print(f"  {line}")
if err.strip():
    print(f"  stderr: {err.strip()[:200]}")
sys.stdout.flush()

section("System-wide HTTPS test — curl.exe")

out, err, rc = run(
    ["curl.exe", "-v", "--max-time", "120",
     "-X", "POST",
     "-H", "Content-Type: application/json",
     "-d", '{"columns":"*","filters":{}}',
     "https://mast.stsci.edu/portal/Mashup/Mashup.asmx/columnsconfig"],
    timeout=150
)
# Print summary lines
for line in out.splitlines() + err.splitlines():
    l = line.strip()
    if any(x in l for x in ("SSL", "TLS", "Connected", "HTTP", "schannel", "certificate",
                           "expire", "subject", "issuer", "Status", "time", "alpn")):
        print(f"  {l}")
    elif "curl" in l and "try" in l.lower():
        print(f"  {l}")
# Print first few body lines
body_lines = [l for l in out.splitlines() if l.strip() and not l.startswith("*") and not l.startswith(">") and not l.startswith("<")]
if body_lines:
    print(f"  Body (first 200 chars): {body_lines[0][:200]}")
sys.stdout.flush()

section("IPv6 status")

out, err, rc = run(["powershell", "-Command",
    "Get-NetAdapterBinding -ComponentID 'ms_tcpip6' | Select-Object Name,Enabled | Format-List"])
for line in out.splitlines():
    line = line.strip()
    if line:
        print(f"  {line}")
sys.stdout.flush()

section("Name Resolution Order (hosts file)")

hosts_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 'drivers', 'etc', 'hosts')
print(f"  Hosts file: {hosts_path}")
try:
    with open(hosts_path) as f:
        lines = f.readlines()
    mast_lines = [l.strip() for l in lines if 'mast' in l.lower() or 'stsci' in l.lower()]
    if mast_lines:
        print(f"  MAST-related entries:")
        for l in mast_lines:
            print(f"    {l}")
    else:
        print(f"  No MAST/STScI entries found")
except Exception as e:
    print(f"  Cannot read: {e}")
sys.stdout.flush()

print("\nDone — diagnostic 5 complete.")
sys.stdout.flush()
