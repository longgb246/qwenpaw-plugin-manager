# QwenPaw Plugin Manager

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![CI](https://github.com/longgb246/qwenpaw-plugin-manager/actions/workflows/ci.yml/badge.svg)](https://github.com/longgb246/qwenpaw-plugin-manager/actions/workflows/ci.yml)
[![GitHub Stars](https://img.shields.io/github/stars/longgb246/qwenpaw-plugin-manager?style=social)](https://github.com/longgb246/qwenpaw-plugin-manager)
[![QwenPaw](https://img.shields.io/badge/QwenPaw-%3E%3D1.1.0-green)](https://github.com/QwenLM/QwenPaw)

A visual plugin management UI for [QwenPaw](https://github.com/QwenLM/QwenPaw) (formerly CoPaw).

> **⚠️ Disclaimer**: This is an **unofficial**, community-maintained plugin. It is **not** affiliated with, endorsed by, or officially supported by the QwenPaw / QwenLM team. Use at your own discretion.

Install, uninstall, enable, and disable plugins directly from the QwenPaw Console sidebar.

## Features

- **Visual Management** — Sidebar page in QwenPaw Console with plugin table
- **Install Plugins** — From GitHub ZIP URL or local path
- **Uninstall Plugins** — With confirmation dialog and automatic cleanup
- **Enable/Disable** — Toggle plugins on/off without removing them
- **Plugin Details** — View metadata, files, entry points, and status
- **Auto Config Detection** — Supports both `.copaw` (legacy) and `.qwenpaw` (new) directories
- **Config Backup** — Backs up `config.json` before any modification

## Screenshots

![Plugin Manager UI](docs/plugin-manager-01.jpg)

## Requirements

- [QwenPaw](https://github.com/QwenLM/QwenPaw) >= 1.1.0 (with dynamic plugin support)
- Python 3.10+

## Installation

### Quick Install (Recommended)

```bash
git clone https://github.com/longgb246/qwenpaw-plugin-manager.git
cd qwenpaw-plugin-manager
bash install.sh
```

### Using QwenPaw CLI

```bash
qwenpaw plugin install /path/to/qwenpaw-plugin-manager
```

### Manual Install

```bash
# Detect your config directory
CONFIG_DIR="$HOME/.copaw"
[ ! -d "$CONFIG_DIR" ] && CONFIG_DIR="$HOME/.qwenpaw"

# Copy plugin files
mkdir -p "$CONFIG_DIR/plugins/plugin-manager"
cp plugin.json plugin.py frontend.js __init__.py "$CONFIG_DIR/plugins/plugin-manager/"

# Restart QwenPaw
qwenpaw shutdown && qwenpaw app
```

## Uninstall

```bash
bash uninstall.sh
```

Or via QwenPaw CLI:

```bash
qwenpaw plugin uninstall plugin-manager
```

## Usage

After installation and restarting QwenPaw:

1. Open QwenPaw Console in your browser
2. Click **🔌 插件管理** in the sidebar
3. View installed plugins, enable/disable, or install new ones

### API Endpoints

The plugin runs a local HTTP server on port `39149`:

| Method | Path | Description |
|--------|------|-------------|
| GET | `/list` | List all installed plugins |
| GET | `/info/<id>` | Get plugin details |
| POST | `/install` | Install a plugin (`{"source": "..."}`) |
| POST | `/uninstall` | Uninstall a plugin (`{"plugin_id": "..."}`) |
| POST | `/toggle` | Enable/disable a plugin (`{"plugin_id": "...", "enabled": true}`) |

## Development

### Dev Mode (Symlink)

For active development, create a symlink instead of copying files:

```bash
make dev
```

This creates a symbolic link from the plugin directory to this repo, so changes are reflected immediately (restart QwenPaw to reload).

### Project Structure

```
qwenpaw-plugin-manager/
├── plugin.json          # Plugin manifest
├── plugin.py            # Backend: HTTP API server (port 39149)
├── frontend.js          # Frontend: React sidebar component
├── __init__.py          # Python package init
├── install.sh           # One-click install script
├── uninstall.sh         # One-click uninstall script
├── Makefile             # Dev shortcuts
├── LICENSE              # MIT License
├── CHANGELOG.md         # Version history
├── CONTRIBUTING.md      # Contributing guide
├── .editorconfig        # Editor settings
├── README.md            # English documentation
├── README_zh.md         # Chinese documentation
├── docs/
│   ├── SCREENSHOTS.md   # Screenshot guide
│   └── plugin-manager-01.jpg  # UI screenshot
└── .github/
    ├── workflows/
    │   └── ci.yml       # CI pipeline
    ├── ISSUE_TEMPLATE/
    │   ├── bug_report.md
    │   └── feature_request.md
    └── pull_request_template.md
```

### Config Directory Detection

The plugin follows QwenPaw's config directory priority:

1. `QWENPAW_WORKING_DIR` environment variable (if set)
2. `~/.copaw` (if exists — legacy installation)
3. `~/.qwenpaw` (default for new installations)

## License

[MIT](LICENSE) © longgb246
