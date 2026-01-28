CREATE VIEW v_recordings_display AS
SELECT
    artist,
    title,
    year,
    COALESCE(composer, '---')      AS composer,
    COALESCE(orchestra, '---')     AS orchestra,
    COALESCE(conductor, '---')     AS conductor,
    genre,
    format,
    COALESCE(label, '---')         AS label,
    COALESCE(catalog_number, '---') AS catalog_number,
    COALESCE(recording_mode, '-')  AS recording_mode,
    COALESCE(reissue, '-')         AS reissue,
    COALESCE(dbx_encoded, '-')     AS dbx_encoded
FROM recordings;

