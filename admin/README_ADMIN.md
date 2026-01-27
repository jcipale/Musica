# Musica – Administrative Setup Guide

This directory contains **privileged, DBA-only scripts** required to initialize
and maintain a Musica database instance.

These scripts **must be executed by a MySQL/MariaDB user with administrative
privileges** (root or equivalent).

They are **not part of normal runtime operation**.

---

## Directory Purpose

The `admin/` directory exists to clearly separate:

- **Database creation & structural changes**
- **Security and privilege management**
- **One-time or destructive initialization tasks**

from application and user-level SQL found in `../sql/`.

This separation is intentional and enforced.

---
## Administrative Utilities Overview

The following scripts are maintained in this directory. All are
administrator-only and may perform destructive operations.

| Script | Purpose |
|------|--------|
| musica_db_cleanup.py | Performs destructive cleanup of database artifacts and residual files. |
| musica_db_backup.py | Creates a full database backup stored under data/archive with a timestamp. |
| musica_db_restore.py | Restores a database from a previously created backup. |
| musica_verify_env.py | Validates directory structure, permissions, configuration, and database availability. |

All scripts assume a correctly configured `config/musica.conf` and
may require elevated privileges.

---

## Files in This Directory

### `musica_db_init.py`
Primary database initialization utility.

Responsibilities:
- Create a new Musica database
- Create a database user
- Grant permissions based on selected role
- Apply required schema objects (staging tables, views)
- Emit a clear audit-style summary on completion

This script is expected to be run:
- once per database
- by a DBA or administrator
- during initial deployment

---

### `Create_Staging.sql`
Creates staging tables required for batch-loading workflows.

Notes:
- Executed **once per database**
- Required for batch CSV loading
- Must be run before any LOAD DATA operations

---

### `v_recordings_display.sql`
Creates user-facing views that normalize display behavior
(e.g., NULL vs placeholder values).

Notes:
- Executed **once per database**
- Views are persistent
- Used automatically by queries (not by insert scripts)

---

## Execution Order (Manual)

If running manually, the correct order is:

1. Create database
2. Create user
3. Grant permissions
4. Apply staging tables
5. Apply views

The `musica_db_init.py` script automates all of the above.

Manual execution of individual SQL files is supported for debugging or recovery, but the Python initializer is the authoritative path for new deployments.

---

## Security Model

- End users **do not** need CREATE or GRANT privileges
- Runtime scripts operate under least privilege
- Structural changes are centralized here

This is by design.

---

## Important Notes

- These scripts are **database-specific**
- Running them on one database does **not** affect others
- Re-running them may fail if objects already exist

## Expected Failure Modes
- Some operations in this directory are intentionally non-idempotent.
- Errors such as “object already exists” or “user already present” are signals, not bugs.
- These utilities favor explicit failure over silent mutation, in keeping with QA and audit best practices.

This is expected behavior.

---

## Intended Audience

This directory is for:
- DBAs
- System administrators
- Deployment automation

It is **not** required for daily Musica operation.

---

Time zones, audit logging, and extended role profiles may be added later.

