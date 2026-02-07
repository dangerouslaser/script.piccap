# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Kodi add-on (`script.piccap`) that toggles the Piccap screen capture service on rooted LG WebOS TVs via SSH. Used with HyperHDR/Hyperion ambient lighting setups. Licensed under MIT.

## Architecture

Single-file Python add-on following Kodi's script add-on structure:

- `default.py` — All logic: SSH command execution, toggle/start/stop actions, Kodi notifications. Entry point is `main()`, which dispatches based on `sys.argv[1]` (start/stop/settings/toggle).
- `addon.xml` — Kodi add-on manifest (id: `script.piccap`, requires `xbmc.python 3.0.0`)
- `resources/settings.xml` — Kodi settings UI definition (v2 schema). Settings: `tv_ip`, `ssh_user`, `ssh_key_path`, `ssh_timeout`.
- `resources/keymap_example.xml` — Example keymap for mapping to a remote button.

## Key Implementation Details

- Communicates with the TV by SSHing in and running `luna-send` commands against `luna://org.webosbrew.piccap.service/{action}` where action is `status`, `start`, or `stop`.
- Toggle checks `"isRunning":true` in the status response to determine current state.
- SSH is invoked via `subprocess.run` with `shell=True`. The command uses `-tt` for pseudo-terminal allocation and `-o StrictHostKeyChecking=no`.
- Settings defaults are handled in `get_settings()` with fallbacks (root user, `/storage/.ssh/id_ed25519` key path, 5s timeout). The `/storage/` path is CoreELEC/LibreELEC-specific.

## Packaging

To create a distributable zip: package all files except `.git/`, `.claude/`, and `CLAUDE.md` into `script.piccap.zip`. The zip must contain files at the root level (not inside a subdirectory).
