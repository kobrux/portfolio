# Network Exposure Scanner

A lightweight scanner that inventories network services on a
CIDR range and highlights risky exposures. Generates JSON and HTML reports that
hiring managers can open without installing special tooling.

## Features

- **Cross-platform Python 3** using asyncio sockets (no Nmap dependency).
- **Curated risky port list** out of the box, configurable via CLI.
- **Banner grabbing** to capture lightweight service fingerprints.
- **Human-friendly reporting**: console summary + optional JSON/HTML artifacts.
- **Safety controls**: concurrency + timeout settings to avoid noisy scans.

## Usage (CLI)

```bash
cd network-exposure-scanner
python3 network_exposure_scanner.py 192.168.1.0/24 \
  --ports 22,80,443,3389 \
  --json report.json \
  --html report.html
```

### Important Flags

| Flag | Description |
|------|-------------|
| `target` | CIDR notation network to scan (required). |
| `--ports` | Comma-separated list or ranges (e.g., `22,80,8000-8100`). |
| `--timeout` | Socket timeout per connection (seconds). |
| `--concurrency` | Maximum simultaneous sockets (default 200). |
| `--json` | Output file for structured data. |
| `--html` | Output file for executive summary. |

## Example Output

```
Target: 192.168.1.0/24
Hosts scanned: 254
Ports: 22, 80, 443

Exposed services detected:
 - 192.168.1.10:22 — SSH-2.0-OpenSSH_9.0
   Risk: Confirm SSH uses keys + disable password logins if possible.
 - 192.168.1.15:80 — Apache httpd
   Risk: HTTP without TLS exposes sessions.
JSON saved to report.json
HTML saved to report.html
```

## GUI Usage

A simple Tkinter GUI wrapper is available if you prefer not to use the terminal.

```bash
cd network-exposure-scanner
python3 scanner_gui.py
```

In the GUI you can:
- Enter a **target CIDR** (for example `192.168.1.0/24`)
- Optionally customize **ports**, **timeout**, and **concurrency**
- Set JSON and HTML report file names
- Click **Run Scan** to start a background scan and see a live log of results

## Ethics & Safety

Use only on networks you own or have explicit permission to test. The scanner is
intentionally conservative and does not exploit vulnerabilities—it simply maps
open services so you can review and harden your own environment.
