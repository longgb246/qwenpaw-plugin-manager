# QwenPaw Plugin Manager

A visual plugin management UI for [QwenPaw](https://github.com/QwenLM/QwenPaw) (formerly CoPaw).

Install, uninstall, enable, and disable plugins directly from the QwenPaw Console sidebar.

## Features

- **Visual Management** — Sidebar page in QwenPaw Console with plugin table
- **Install Plugins** — From GitHub ZIP URL or local path
- **Uninstall Plugins** — With confirmation dialog and automatic cleanup
- **Enable/Disable** — Toggle plugins on/off without removing them
- **Plugin Details** — View metadata, files, entry points, and status
- **Auto Config Detection** — Supports both `.copaw` (legacy) and `.qwenpaw` (new) directories
- **Config Backup** — Backs up `config.json` before any modification

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
├── plugin.json      # Plugin manifest
├── plugin.py        # Backend: HTTP API server (port 39149)
├── frontend.js      # Frontend: React sidebar component
├── __init__.py      # Python package init
├── install.sh       # One-click install script
├── uninstall.sh     # One-click uninstall script
├── Makefile         # Dev shortcuts
├── LICENSE          # MIT License
├── CHANGELOG.md     # Version history
├── README.md        # This file (English)
└── README_zh.md     # Chinese documentation
```

### Config Directory Detection

The plugin follows QwenPaw's config directory priority:

1. `QWENPAW_WORKING_DIR` environment variable (if set)
2. `~/.copaw` (if exists — legacy installation)
3. `~/.qwenpaw` (default for new installations)

## License

[MIT](LICENSE) © longgb246
