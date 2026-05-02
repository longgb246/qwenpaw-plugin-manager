# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-05-02

### Added

- Initial release of QwenPaw Plugin Manager
- Visual plugin management UI in QwenPaw Console sidebar
- Plugin listing with status display (enabled/disabled/missing)
- Install plugins from URL (ZIP) or local path
- Uninstall plugins with confirmation dialog
- Enable/disable plugins toggle
- Plugin detail modal with file listing
- Standalone HTTP API server on port 39149
- Auto-detection of config directory (`.copaw` / `.qwenpaw`)
- One-click install/uninstall shell scripts
- Compatible with both legacy `.copaw` and new `.qwenpaw` configurations
- PROFILE.md cleanup on plugin uninstall
- Config backup before modifications
