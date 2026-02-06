-- Create_Staging.sql — Staging Table: stg_recordings

CREATE TABLE IF NOT EXISTS stg_recordings (
    stg_id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    load_batch_id    BIGINT NOT NULL,
    source_file      VARCHAR(255) NOT NULL,

    artist           VARCHAR(255) NOT NULL,
    title            VARCHAR(255) NOT NULL,
    year             INT NOT NULL,

    composer         VARCHAR(255),
    orchestra        VARCHAR(255),
    conductor        VARCHAR(255),

    genre            VARCHAR(50) NOT NULL,
    format           VARCHAR(20) NOT NULL,
    label            VARCHAR(100),
    catalog_number   VARCHAR(50),

    recording_mode   CHAR(1),
    reissue          CHAR(1),
    dbx_encoded      CHAR(1),

    is_valid         TINYINT(1) NOT NULL DEFAULT 1,
    validation_errors VARCHAR(255),

    INDEX idx_stg_batch_valid (load_batch_id, is_valid)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;

