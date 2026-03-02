-- Create_Staging_sqlite.sql — Staging Table: stg_recordings
-- SQLite 3.x

CREATE TABLE IF NOT EXISTS stg_recordings (
    stg_id             INTEGER PRIMARY KEY,
    load_batch_id      INTEGER NOT NULL,
    source_file        TEXT NOT NULL,

    artist             TEXT NOT NULL,
    title              TEXT NOT NULL,
    year               INTEGER NOT NULL,

    composer           TEXT,
    orchestra          TEXT,
    conductor          TEXT,

    genre              TEXT NOT NULL,
    format             TEXT NOT NULL,
    label              TEXT,
    catalog_number     TEXT,

    recording_mode     TEXT,   -- expected M/S/B or NULL (validate later)
    reissue            TEXT,   -- expected Y/N or NULL
    dbx_encoded        TEXT,   -- expected Y or NULL

    is_valid           INTEGER NOT NULL DEFAULT 1
        CHECK (is_valid IN (0,1)),

    validation_errors  TEXT
);

CREATE INDEX IF NOT EXISTS idx_stg_batch_valid
ON stg_recordings (load_batch_id, is_valid);

