## Portfolio

A few fun projects

### Wi-Fi Channel Viewer (`wifi-channel-tool/`)

Cross-platform Python tools that show which Wi‑Fi channel the current network is using.

- **CLI**: `network_channel.py`  
  Prints the current Wi‑Fi channel in the terminal.
- **GUI**: `network_channel_gui.py`  
  Small Tkinter window with a “Refresh” button that displays the current Wi‑Fi channel.

#### Requirements
- Python 3.10+ installed
- macOS or Linux

#### Run the CLI
```bash
cd wifi-channel-tool
chmod +x network_channel.py      # first time only
./network_channel.py
```

#### Run the GUI
```bash
cd wifi-channel-tool
chmod +x network_channel_gui.py  # first time only
./network_channel_gui.py
```

On macOS, the tools will:
- Prefer the `airport` command if available.
- Fall back to `system_profiler SPAirPortDataType` when `airport` is missing.

On Linux, they use:
- `nmcli` (NetworkManager) when present.
- `iwconfig` as a fallback.

### Network Exposure Scanner (`network-exposure-scanner/`)

Map exposed services across a CIDR range using asynchronous sockets, banner
grabbing, and automatically generated HTML/JSON reports. 

#### Run the CLI

```bash
cd network-exposure-scanner
python3 network_exposure_scanner.py 192.168.1.0/24 \\
  --ports 22,80,443,3389 \\
  --json report.json \\
  --html report.html
```

#### Run the GUI

```bash
cd network-exposure-scanner
python3 scanner_gui.py
```
