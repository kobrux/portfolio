## Portfolio

Curated projects that showcase practical scripting and application skills.

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
