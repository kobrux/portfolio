#!/usr/bin/env python3
"""Show the Wi-Fi channel for the currently connected network."""
from __future__ import annotations

import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional


def run_command(command: list[str]) -> str:
    """Run command and return stdout, raising a helpful error on failure."""
    try:
        return subprocess.check_output(command, text=True)
    except FileNotFoundError:
        raise RuntimeError(f"Command not found: {' '.join(command)}") from None
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            f"Command {' '.join(command)} failed with exit code {exc.returncode}:\n{exc.output}"
        ) from exc


def parse_channel_from_airport(output: str) -> Optional[str]:
    match = re.search(r"channel:\s*(.+)", output)
    if match:
        # Some macOS versions show values like "149,1" → we only need the channel number
        return match.group(1).strip().split(",")[0]
    return None


def parse_channel_from_nmcli(output: str) -> Optional[str]:
    for line in output.splitlines():
        # Active connections look like: "yes:44" or "yes:11"
        active, _, channel = line.partition(":")
        if active == "yes" and channel:
            return channel.strip()
    return None


def parse_channel_from_iwconfig(output: str) -> Optional[str]:
    match = re.search(r"Channel[:=](\d+)", output)
    if match:
        return match.group(1)
    return None


def _find_airport_binary() -> Optional[str]:
    """Return a usable path to Apple's airport CLI if available."""
    candidates: list[str] = []
    airport_in_path = shutil.which("airport")
    if airport_in_path:
        candidates.append(airport_in_path)
    candidates.extend(
        [
            "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport",
            "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/A/Resources/airport",
        ]
    )

    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    return None


def _get_channel_via_system_profiler() -> Optional[str]:
    """Fallback that parses `system_profiler SPAirPortDataType` output."""
    try:
        output = run_command(["/usr/sbin/system_profiler", "SPAirPortDataType"])
    except RuntimeError:
        return None

    match = re.search(r"Channel:\s*(\d+)", output)
    if match:
        return match.group(1)
    return None


def get_channel() -> str:
    system = platform.system().lower()

    if system == "darwin":
        airport_cmd = _find_airport_binary()
        if airport_cmd:
            output = run_command([airport_cmd, "-I"])
            channel = parse_channel_from_airport(output)
            if channel:
                return channel
        channel = _get_channel_via_system_profiler()
        if channel:
            return channel
        raise RuntimeError(
            "Unable to determine Wi-Fi channel. The airport utility is missing and "
            "`system_profiler` did not report a channel. Try installing Apple "
            "Command Line Tools (`xcode-select --install`)."
        )

    if system == "linux":
        nmcli = shutil.which("nmcli")
        if nmcli:
            output = run_command([nmcli, "-t", "-f", "active,chan", "dev", "wifi"])
            channel = parse_channel_from_nmcli(output)
            if channel:
                return channel
        iwconfig = shutil.which("iwconfig")
        if iwconfig:
            output = run_command([iwconfig])
            channel = parse_channel_from_iwconfig(output)
            if channel:
                return channel
        raise RuntimeError("Neither nmcli nor iwconfig provided channel information.")

    raise RuntimeError("Unsupported operating system. This tool supports macOS and Linux.")


def main() -> None:
    try:
        channel = get_channel()
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Current Wi-Fi channel: {channel}")


if __name__ == "__main__":
    main()
