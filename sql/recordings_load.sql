LOAD DATA LOCAL INFILE '/opt/Musica/data/imports/recordings_load.csv'
INTO TABLE stg_recordings
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(
    artist,
    title,
    year,
    orchestra,
    conductor,
    genre,
    format,
    label,
    catalog_number,
    reissue,
    recording_mode,
    dbx_encoded
);

