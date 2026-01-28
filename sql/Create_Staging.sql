
CREATE TABLE stg_recordings (
    -- =========================
    -- Business columns (MUST mirror recordings)
    -- =========================
    artist            VARCHAR(255) NOT NULL,
    title             VARCHAR(255) NOT NULL,
    year              INT NOT NULL,

    composer          VARCHAR(255),
    orchestra         VARCHAR(255),
    conductor         VARCHAR(255),

    genre             VARCHAR(50) NOT NULL,
    format            VARCHAR(20) NOT NULL,
    label             VARCHAR(100),
    catalog_number    VARCHAR(50),

    recording_mode    CHAR(1),
    reissue           CHAR(1),
    dbx_encoded       CHAR(1),

    -- =========================
    -- Staging / load control
    -- =========================
    stg_id            BIGINT AUTO_INCREMENT PRIMARY KEY,
    load_batch_id     BIGINT NOT NULL,
    source_file       VARCHAR(255) NOT NULL,

    -- =========================
    -- Validation status
    -- =========================
    is_valid          TINYINT(1) NOT NULL DEFAULT 1,
    validation_errors VARCHAR(255),

    -- =========================
    -- Optional operational index
    -- =========================
    INDEX idx_stg_batch_valid (load_batch_id, is_valid)
);

