#!/usr/bin/env python3
"""Network Exposure Scanner.

Scans a CIDR range for common service ports, highlights risky exposures,
and produces JSON/HTML summaries suitable for portfolio demos.

This is intentionally polite (configurable concurrency + timeout) so it can be
used on lab networks without overwhelming equipment. Always get permission
before scanning networks you don't own.
"""
from __future__ import annotations

import argparse
import asyncio
import ipaddress
import json
import os
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Sequence


DEFAULT_PORTS = [
    21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 389,
    443, 445, 465, 587, 993, 995, 1433, 1521, 1723,
    3306, 3389, 5432, 5900, 6379, 8080, 8443
]

RISK_NOTES = {
    21: "FTP transmits credentials in plain text.",
    22: "Confirm SSH uses keys + disable password logins if possible.",
    23: "Telnet is insecure; replace with SSH.",
    25: "Ensure SMTP is authenticated to prevent open relay abuse.",
    80: "HTTP without TLS exposes sessions.",
    135: "RPC often exploited by worms; limit to trusted hosts.",
    139: "Legacy SMB over NetBIOS; disable if not required.",
    443: "Verify TLS configuration and certificates.",
    445: "SMB over TCP. Patch against EternalBlue-style exploits.",
    1433: "SQL Server exposed—enforce strong auth & network ACLs.",
    3306: "MySQL open to network. Restrict to application subnets.",
    3389: "RDP exposed. Require MFA + gateway/VPN.",
    5900: "VNC typically unencrypted. Use SSH tunnel or disable.",
    6379: "Redis unauthenticated by default; bind to localhost.",
    8080: "Check for admin consoles left exposed.",
}


@dataclass
class Exposure:
    host: str
    port: int
    service_banner: str | None
    risk: str | None


@dataclass
class ScanReport:
    target: str
    ports: Sequence[int]
    host_count: int
    exposures: List[Exposure]
    started_at: str
    finished_at: str

    def to_json(self) -> str:
        return json.dumps(
            {
                "target": self.target,
                "ports": list(self.ports),
                "host_count": self.host_count,
                "started_at": self.started_at,
                "finished_at": self.finished_at,
                "exposures": [asdict(exp) for exp in self.exposures],
            },
            indent=2,
        )


async def scan_port(
    ip: str,
    port: int,
    timeout: float,
    semaphore: asyncio.Semaphore,
) -> Exposure | None:
    """Attempt to connect to ip:port and capture a short banner."""
    try:
        async with semaphore:
            reader: asyncio.StreamReader
            writer: asyncio.StreamWriter
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port),
                timeout=timeout,
            )
            try:
                await asyncio.wait_for(writer.drain(), timeout=timeout)
                # Send a newline to coax banners for some protocols.
                writer.write(b"\n")
                await asyncio.wait_for(writer.drain(), timeout=timeout)
                try:
                    banner = await asyncio.wait_for(reader.read(64), timeout=timeout)
                except TimeoutError:
                    banner = b""
            finally:
                writer.close()
                await writer.wait_closed()
    except (asyncio.TimeoutError, ConnectionError, OSError):
        return None

    banner_text = banner.decode(errors="ignore").strip() if banner else None
    return Exposure(
        host=ip,
        port=port,
        service_banner=banner_text,
        risk=RISK_NOTES.get(port),
    )


async def scan_network(
    target_cidr: str,
    ports: Sequence[int],
    timeout: float,
    concurrency: int,
) -> List[Exposure]:
    net = ipaddress.ip_network(target_cidr, strict=False)
    ips = [str(host) for host in net.hosts()]
    semaphore = asyncio.Semaphore(concurrency)
    tasks: list[asyncio.Task[Exposure | None]] = []
    for ip in ips:
        for port in ports:
            tasks.append(asyncio.create_task(scan_port(ip, port, timeout, semaphore)))
    exposures: List[Exposure] = []
    for task in asyncio.as_completed(tasks):
        result = await task
        if result:
            exposures.append(result)
    return exposures


def parse_ports(raw: str | None) -> List[int]:
    if not raw:
        return DEFAULT_PORTS
    ports: List[int] = []
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "-" in chunk:
            start_s, end_s = chunk.split("-", 1)
            start, end = int(start_s), int(end_s)
            ports.extend(range(start, end + 1))
        else:
            ports.append(int(chunk))
    return sorted(set(port for port in ports if 1 <= port <= 65535))


def write_html(report: ScanReport, output_path: Path) -> None:
    rows = []
    for exp in report.exposures:
        rows.append(
            f"<tr><td>{exp.host}</td><td>{exp.port}</td><td>{exp.service_banner or '-'}" \
            f"</td><td>{exp.risk or 'Review manually'}</td></tr>"
        )
    table_rows = "\n".join(rows) or "<tr><td colspan='4'>No exposures detected</td></tr>"
    html = f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <title>Network Exposure Report</title>
  <style>
    body {{ font-family: -apple-system, 'Segoe UI', sans-serif; margin: 2rem; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ddd; padding: 0.5rem; }}
    th {{ background: #f3f4f6; text-align: left; }}
  </style>
</head>
<body>
  <h1>Network Exposure Report</h1>
  <p><strong>Target:</strong> {report.target}</p>
  <p><strong>Hosts scanned:</strong> {report.host_count}</p>
  <p><strong>Ports:</strong> {', '.join(map(str, report.ports))}</p>
  <p><strong>Scan window:</strong> {report.started_at} → {report.finished_at}</p>
  <table>
    <thead>
      <tr><th>Host</th><th>Port</th><th>Banner</th><th>Risk Note</th></tr>
    </thead>
    <tbody>
      {table_rows}
    </tbody>
  </table>
</body>
</html>
"""
    output_path.write_text(html, encoding="utf-8")


def run_cli() -> None:
    parser = argparse.ArgumentParser(
        description="Scan a network for exposed services and generate a report.",
    )
    parser.add_argument("target", help="CIDR range, e.g. 192.168.1.0/24")
    parser.add_argument(
        "--ports",
        help="Comma-separated ports and ranges (e.g. 22,80,443,1000-1010)."
             " Defaults to a curated list of risky services.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=1.0,
        help="Socket timeout in seconds (default: 1.0).",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=200,
        help="Maximum simultaneous connection attempts (default: 200).",
    )
    parser.add_argument(
        "--json",
        type=Path,
        help="Optional path to write JSON report.",
    )
    parser.add_argument(
        "--html",
        type=Path,
        help="Optional path to write HTML report.",
    )
    args = parser.parse_args()

    ports = parse_ports(args.ports)
    if not ports:
        parser.error("No valid ports supplied.")

    start = datetime.utcnow()
    try:
        exposures = asyncio.run(
            scan_network(args.target, ports, args.timeout, args.concurrency)
        )
    except KeyboardInterrupt:
        print("Scan interrupted by user.")
        sys.exit(1)
    stop = datetime.utcnow()

    report = ScanReport(
        target=args.target,
        ports=ports,
        host_count=sum(1 for _ in ipaddress.ip_network(args.target, strict=False).hosts()),
        exposures=exposures,
        started_at=start.isoformat() + "Z",
        finished_at=stop.isoformat() + "Z",
    )

    # Print summary
    print(f"Target: {report.target}")
    print(f"Hosts scanned: {report.host_count}")
    print(f"Ports: {', '.join(map(str, ports))}")
    if report.exposures:
        print("\nExposed services detected:")
        for exp in report.exposures:
            banner_display = f" — {exp.service_banner}" if exp.service_banner else ""
            print(f" - {exp.host}:{exp.port}{banner_display}")
            if exp.risk:
                print(f"   Risk: {exp.risk}")
    else:
        print("\nNo exposed services detected on the selected ports.")

    if args.json:
        args.json.write_text(report.to_json(), encoding="utf-8")
        print(f"JSON saved to {args.json}")
    if args.html:
        write_html(report, args.html)
        print(f"HTML saved to {args.html}")


if __name__ == "__main__":
    run_cli()
