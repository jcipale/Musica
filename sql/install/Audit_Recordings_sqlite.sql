-- Audit_Recordings_sqlite.sql — audit_recordings
-- SQLite 3.x

CREATE TABLE IF NOT EXISTS audit_recordings (
    audit_id     INTEGER PRIMARY KEY,
    recording_id INTEGER,

    action       TEXT
        CHECK (action IN ('INSERT','UPDATE','DELETE')),

    action_ts    TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),

    user_name    TEXT,
    notes        TEXT
);

-- Optional but recommended index for lookups by recording_id
CREATE INDEX IF NOT EXISTS idx_audit_recordings_recording_id
ON audit_recordings (recording_id);

