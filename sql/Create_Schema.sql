-- Create_Schema.sql — Production Table: recordings
-- MariaDB 10.6+ / utf8mb4 / InnoDB

CREATE DATABASE IF NOT EXISTS Musica
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE Musica;

CREATE TABLE IF NOT EXISTS recordings (
    id               BIGINT AUTO_INCREMENT PRIMARY KEY,

    artist           VARCHAR(255) NOT NULL,
    title            VARCHAR(255) NOT NULL,
    year             INT NOT NULL CHECK (year >= 1900 AND year <= YEAR(CURDATE()) + 1),

    composer         VARCHAR(255) DEFAULT '---',
    orchestra        VARCHAR(255) DEFAULT '---',
    conductor        VARCHAR(255) DEFAULT '---',

    genre            ENUM('Jazz','Rock','Country','Symphonic') NOT NULL,
    format           ENUM('LP','CD','Cass','RtR','78','4T','8T') NOT NULL,
    label            VARCHAR(100) DEFAULT '---',
    catalog_number   VARCHAR(50) DEFAULT '---',

    recording_mode   ENUM('M','S') DEFAULT NULL,
    reissue          ENUM('Y','N') DEFAULT NULL,
    dbx_encoded      ENUM('Y') DEFAULT NULL,

    -- Index for lookups; duplicates allowed
    INDEX idx_artist_title_year (artist, title, year)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;

-- Trigger: prevent future-year entries
DELIMITER //

CREATE TRIGGER trg_recordings_year_ins
BEFORE INSERT ON recordings
FOR EACH ROW
BEGIN
    IF NEW.year > YEAR(CURDATE()) + 1 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid year: exceeds allowed range';
    END IF;
END//

CREATE TRIGGER trg_recordings_year_upd
BEFORE UPDATE ON recordings
FOR EACH ROW
BEGIN
    IF NEW.year > YEAR(CURDATE()) + 1 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid year: exceeds allowed range';
    END IF;
END//

DELIMITER ;

