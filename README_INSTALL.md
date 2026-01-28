# Musica – Installation & Uninstallation Utilities

This directory contains **privileged system-level utilities** used to install,
upgrade, or completely remove the Musica application from a system.

These scripts are **not part of normal runtime operation**.

They must be executed by a system administrator with root privileges.

---

## Overview

Musica uses explicit, auditable installation and removal scripts to ensure:

- Predictable filesystem layout
- Version-aware upgrades
- Clear failure behavior
- No silent data loss
- No hidden side effects

All destructive actions require confirmation.

---

## Scripts

### install.py

Primary installation and upgrade utility.

#### Responsibilities
- Verify root privileges
- Validate source package integrity
- Detect existing installation
- Compare VERSION files
- Prompt before overwriting identical versions
- Abort if installed version is newer
- Create full directory hierarchy under `/opt/Musica`
- Copy project files into place
- Remove source directories after install
- Write detailed install logs
- Remove the original tarball after successful install

#### Behavior Notes
- Installation target is fixed at `/opt/Musica`
- Logging is written to `/opt/Musica/logs/`
- Version comparison is string-based
- Installer favors explicit failure over recovery

#### Typical Usage
```sh
sudo ./install.py

