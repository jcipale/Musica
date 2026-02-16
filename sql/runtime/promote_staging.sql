-- promote_staging.sql — Promote valid staging rows to recordings

INSERT IGNORE INTO recordings (
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
    COALESCE(NULLIF(TRIM(composer), ''), NULL),
    COALESCE(NULLIF(TRIM(orchestra), ''), NULL),
    COALESCE(NULLIF(TRIM(conductor), ''), NULL),
    genre,
    format,
    COALESCE(NULLIF(TRIM(label), ''), NULL),
    COALESCE(NULLIF(TRIM(catalog_number), ''), NULL),
    UPPER(NULLIF(TRIM(recording_mode), '')) AS recording_mode,
    UPPER(NULLIF(TRIM(reissue), ''))        AS reissue,
    UPPER(NULLIF(TRIM(dbx_encoded), ''))    AS dbx_encoded
FROM stg_recordings
WHERE is_valid = 1;

