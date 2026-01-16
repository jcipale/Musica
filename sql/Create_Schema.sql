-- Create_Schema.sql
-- Phase 2 schema — MariaDB 10.5+ enforced

-- USE Musica; (<-- removed for debug/defect tracking purposes)

CREATE TABLE recordings (
    id                INT AUTO_INCREMENT PRIMARY KEY,

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

    CONSTRAINT uq_artist_title_year
        UNIQUE (artist, title, year),

    CONSTRAINT chk_year_lower_bound
        CHECK (year >= 1900),

    CONSTRAINT chk_genre
        CHECK (genre IN ('Jazz','Rock','Country','Symphonic')),

    CONSTRAINT chk_format
        CHECK (format IN ('LP','CD','Cass','RtR')),

	CONSTRAINT chk_recording_mode
        CHECK (recording_mode IN ('M','S') OR recording_mode IS NULL),

    CONSTRAINT chk_dbx
        CHECK (dbx_encoded = 'Y' OR dbx_encoded IS NULL),

    CONSTRAINT chk_reissue
        CHECK (reissue IN ('Y','N') OR reissue IS NULL)
);

DELIMITER //

CREATE TRIGGER trg_recordings_year_ins
BEFORE INSERT ON recordings
FOR EACH ROW
BEGIN
    IF NEW.year > YEAR(CURDATE()) + 1 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Invalid year: exceeds allowed range';
    END IF;
END//

CREATE TRIGGER trg_recordings_year_upd
BEFORE UPDATE ON recordings
FOR EACH ROW
BEGIN
    IF NEW.year > YEAR(CURDATE()) + 1 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Invalid year: exceeds allowed range';
    END IF;
END//

DELIMITER ;

