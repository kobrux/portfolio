# Network Exposure Scanner

A lightweight, portfolio-friendly scanner that inventories network services on a
CIDR range and highlights risky exposures. Generates JSON and HTML reports that
hiring managers can open without installing special tooling.

## Features

- **Cross-platform Python 3** using asyncio sockets (no Nmap dependency).
- **Curated risky port list** out of the box, configurable via CLI.
- **Banner grabbing** to capture lightweight service fingerprints.
- **Human-friendly reporting**: console summary + optional JSON/HTML artifacts.
- **Safety controls**: concurrency + timeout settings to avoid noisy scans.

## Usage

```bash
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

## Ethics & Safety

Use only on networks you own or have explicit permission to test. The scanner is
intentionally conservative and does not exploit vulnerabilities—it simply maps
open services so you can discuss potential mitigations in interviews.

## Portfolio Talking Points

- Explain how asyncio and semaphores keep scans efficient yet polite.
- Discuss the risk heuristic and how you’d expand it (e.g., CVE lookups).
- Mention potential future work: integration with Shodan, scheduling, or
  authenticated scans within lab environments.
