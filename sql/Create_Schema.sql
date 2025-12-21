-- Create_Schema.sql
-- Phase 3B schema — requires empty database

USE Musica;

CREATE TABLE recordings (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    artist          VARCHAR(255) NOT NULL,
    title           VARCHAR(255) NOT NULL,
    orchestra       VARCHAR(255),
    conductor       VARCHAR(255),
    year            INT,
    genre           VARCHAR(50),
    format          VARCHAR(20),
    label           VARCHAR(100),
    catalog_number  VARCHAR(50),
    reissue         CHAR(1),
    mode            CHAR(1),
    dbx             CHAR(1),
    UNIQUE KEY uq_recording (
        artist,
        title,
        year,
        format,
        catalog_number
    )
);

