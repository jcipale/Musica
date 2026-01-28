# Musica – Uninstallation Utility

This directory contains a **privileged system-level utility** used to completely
remove the Musica application from a system.

This script is **not part of normal runtime operation**.

It must be executed by a system administrator with root privileges.

---

## Overview

Musica provides an explicit uninstallation script to ensure:

- Predictable and complete removal
- Clear user intent before destructive actions
- Auditable uninstall behavior
- No silent filesystem mutation
- No partial or ambiguous cleanup

All destructive actions require explicit confirmation.

---

## Script

### uninstall.py

Primary uninstallation utility.

#### Responsibilities
- Verify root privileges
- Validate the presence of a valid Musica installation
- Confirm installation integrity via VERSION file
- Require full-word confirmation before proceeding
- Write a detailed uninstall log
- Remove the entire `/opt/Musica` directory tree

#### Behavior Notes
- Uninstall target is fixed at `/opt/Musica`
- Logging is written to `/opt/Musica/logs/`
- Confirmation requires an **exact text match**
- Script favors explicit failure over partial cleanup

#### Out-of-Scope Actions
- Does not drop databases or schemas
- Does not remove database users
- Does not stop database services
- Does not modify data outside `/opt/Musica`

Database removal is handled separately by administrative utilities
documented in `README_ADMIN.md`.

---

## Typical Usage

```sh
sudo ./uninstall.py

