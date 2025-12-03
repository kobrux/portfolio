#!/usr/bin/env python3
"""Simple Tkinter UI wrapper for network_exposure_scanner.

Lets the user:
- Enter target CIDR
- Pick ports / timeout / concurrency
- Run scan in a background thread
- See a live log and where reports were written
"""
from __future__ import annotations

import asyncio
import ipaddress
import threading
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, scrolledtext
from pathlib import Path

import network_exposure_scanner as core


class ScannerGUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Network Exposure Scanner")
        self.geometry("640x480")
        self.resizable(False, False)

        self._build_form()
        self._build_log()
        self._scan_thread: threading.Thread | None = None

    def _build_form(self) -> None:
        frame = tk.Frame(self)
        frame.pack(padx=16, pady=12, fill=tk.X)

        # Target
        tk.Label(frame, text="Target CIDR:").grid(row=0, column=0, sticky="w")
        self.target_var = tk.StringVar(value="192.168.1.0/24")
        tk.Entry(frame, textvariable=self.target_var, width=30).grid(row=0, column=1, sticky="w")

        # Ports
        tk.Label(frame, text="Ports (optional):").grid(row=1, column=0, sticky="w", pady=(4, 0))
        self.ports_var = tk.StringVar(value="22,80,443,3389")
        tk.Entry(frame, textvariable=self.ports_var, width=30).grid(row=1, column=1, sticky="w", pady=(4, 0))
        tk.Label(frame, text="Leave empty for default risky ports").grid(row=1, column=2, sticky="w", padx=(8, 0))

        # Timeout
        tk.Label(frame, text="Timeout (s):").grid(row=2, column=0, sticky="w", pady=(4, 0))
        self.timeout_var = tk.StringVar(value="1.0")
        tk.Entry(frame, textvariable=self.timeout_var, width=8).grid(row=2, column=1, sticky="w", pady=(4, 0))

        # Concurrency
        tk.Label(frame, text="Concurrency:").grid(row=3, column=0, sticky="w", pady=(4, 0))
        self.conc_var = tk.StringVar(value="200")
        tk.Entry(frame, textvariable=self.conc_var, width=8).grid(row=3, column=1, sticky="w", pady=(4, 0))

        # Output paths
        tk.Label(frame, text="JSON report:").grid(row=4, column=0, sticky="w", pady=(4, 0))
        self.json_var = tk.StringVar(value="report.json")
        tk.Entry(frame, textvariable=self.json_var, width=30).grid(row=4, column=1, sticky="w", pady=(4, 0))

        tk.Label(frame, text="HTML report:").grid(row=5, column=0, sticky="w", pady=(4, 0))
        self.html_var = tk.StringVar(value="report.html")
        tk.Entry(frame, textvariable=self.html_var, width=30).grid(row=5, column=1, sticky="w", pady=(4, 0))

        # Buttons
        btn_frame = tk.Frame(frame)
        btn_frame.grid(row=6, column=0, columnspan=3, pady=(10, 0), sticky="w")

        self.scan_btn = tk.Button(btn_frame, text="Run Scan", command=self.start_scan)
        self.scan_btn.pack(side=tk.LEFT)

    def _build_log(self) -> None:
        log_frame = tk.Frame(self)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(4, 16))

        tk.Label(log_frame, text="Log:").pack(anchor="w")
        self.log = scrolledtext.ScrolledText(log_frame, height=18, state="disabled")
        self.log.pack(fill=tk.BOTH, expand=True)

    def log_line(self, text: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def start_scan(self) -> None:
        if self._scan_thread and self._scan_thread.is_alive():
            messagebox.showinfo("Scan running", "A scan is already in progress.")
            return

        target = self.target_var.get().strip()
        if not target:
            messagebox.showerror("Input error", "Please enter a target CIDR (e.g. 192.168.1.0/24).")
            return

        # Basic validation of CIDR
        try:
            ip_net = ipaddress.ip_network(target, strict=False)
        except ValueError as exc:
            messagebox.showerror("Input error", f"Invalid CIDR: {exc}")
            return

        try:
            timeout = float(self.timeout_var.get())
            concurrency = int(self.conc_var.get())
        except ValueError:
            messagebox.showerror("Input error", "Timeout must be a number and concurrency an integer.")
            return

        ports_raw = self.ports_var.get().strip() or None
        ports = core.parse_ports(ports_raw)
        if not ports:
            messagebox.showerror("Input error", "No valid ports parsed.")
            return

        json_path = Path(self.json_var.get().strip() or "report.json")
        html_path = Path(self.html_var.get().strip() or "report.html")

        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

        self.scan_btn.config(state="disabled")
        self.log_line(f"Starting scan of {target} at {datetime.utcnow().isoformat()}Z")
        self.log_line(f"Hosts: {sum(1 for _ in ip_net.hosts())}, Ports: {', '.join(map(str, ports))}")

        def worker() -> None:
            try:
                exposures = asyncio.run(
                    core.scan_network(str(ip_net), ports, timeout, concurrency)
                )
                report = core.ScanReport(
                    target=str(ip_net),
                    ports=ports,
                    host_count=sum(1 for _ in ip_net.hosts()),
                    exposures=exposures,
                    started_at=datetime.utcnow().isoformat() + "Z",
                    finished_at=datetime.utcnow().isoformat() + "Z",
                )
                json_path.write_text(report.to_json(), encoding="utf-8")
                core.write_html(report, html_path)

                def done() -> None:
                    self.log_line("Scan complete.")
                    if report.exposures:
                        self.log_line("Exposed services detected:")
                        for exp in report.exposures:
                            banner_display = f" — {exp.service_banner}" if exp.service_banner else ""
                            self.log_line(f" - {exp.host}:{exp.port}{banner_display}")
                            if exp.risk:
                                self.log_line(f"   Risk: {exp.risk}")
                    else:
                        self.log_line("No exposed services detected on the selected ports.")
                    self.log_line(f"JSON report: {json_path.resolve()}")
                    self.log_line(f"HTML report: {html_path.resolve()}")
                    self.scan_btn.config(state="normal")

                self.after(0, done)
            except Exception as exc:  # noqa: BLE001
                def failed() -> None:
                    self.log_line(f"Error: {exc}")
                    messagebox.showerror("Scan failed", str(exc))
                    self.scan_btn.config(state="normal")

                self.after(0, failed)

        self._scan_thread = threading.Thread(target=worker, daemon=True)
        self._scan_thread.start()


def main() -> None:
    app = ScannerGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
