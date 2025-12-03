# Wi-Fi Channel Viewer

Tools for checking which channel your current Wi-Fi network is using. Includes a CLI and a Tkinter GUI so interviewers can see both scripting and desktop UI skills.

## Contents

- `network_channel.py` – cross-platform CLI (macOS + Linux) that prints the current Wi-Fi channel.
- `network_channel_gui.py` – simple Tkinter GUI with a refresh button.

## Features

- macOS support via either the `airport` utility or `system_profiler` fallback.
- Linux support using `nmcli` (preferred) or `iwconfig` as a fallback.
- Helpful error messages when dependencies are missing.
- Same detection logic is shared across CLI and GUI.

## Running the CLI

```bash
chmod +x network_channel.py
./network_channel.py
```

## Running the GUI

```bash
chmod +x network_channel_gui.py
./network_channel_gui.py
```

On macOS, make sure Command Line Tools are installed if you want the `airport` binary: `xcode-select --install`. Otherwise the scripts will fall back to `system_profiler`.

## Packaging Notes

This folder is meant to live inside a broader "portfolio" repository you can share with hiring managers. Feel free to add screenshots, tests, or more utilities alongside it.
