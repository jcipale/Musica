-- v_recordings_display_sqlite.sql — Read-only view for display
-- SQLite 3.x

DROP VIEW IF EXISTS v_recordings_display;

CREATE VIEW v_recordings_display AS
SELECT
    artist,
    title,
    year,
    COALESCE(composer, '-')        AS composer,
    COALESCE(orchestra, '-')       AS orchestra,
    COALESCE(conductor, '-')       AS conductor,
    genre,
    format,
    label,
    catalog_number,
    COALESCE(recording_mode, '-')  AS recording_mode,
    COALESCE(reissue, '-')         AS reissue,
    COALESCE(dbx_encoded, '-')     AS dbx_encoded
FROM recordings;

