-- promote_staging_sqlite.sql — Promote valid staging rows to recordings (SQLite)

INSERT INTO recordings (
    artist,
    title,
    year,
    composer,
    orchestra,
    conductor,
    genre,
    format,
    label,
    catalog_number,
    recording_mode,
    reissue,
    dbx_encoded
)
SELECT
    artist,
    title,
    year,
    NULLIF(TRIM(composer), ''),
    NULLIF(TRIM(orchestra), ''),
    NULLIF(TRIM(conductor), ''),
    genre,
    format,
    NULLIF(TRIM(label), ''),
    NULLIF(TRIM(catalog_number), ''),
    UPPER(NULLIF(TRIM(recording_mode), '')) AS recording_mode,
    UPPER(NULLIF(TRIM(reissue), ''))        AS reissue,
    UPPER(NULLIF(TRIM(dbx_encoded), ''))    AS dbx_encoded
FROM stg_recordings
WHERE is_valid = 1;

