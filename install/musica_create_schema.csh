-- Musica Database Schema
-- Compatible with MariaDB, MySQL, SQLite

CREATE DATABASE IF NOT EXISTS Musica;
USE Musica;

CREATE TABLE IF NOT EXISTS ArtistCatalog (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    ArtistLast      VARCHAR(128) NOT NULL,
    ArtistFirst     VARCHAR(128),
    Title           VARCHAR(256) NOT NULL,
    Orchestra       VARCHAR(256),
    Conductor       VARCHAR(128),
    Year            INTEGER,
    Genre           VARCHAR(64),
    Format          VARCHAR(32),
    Label           VARCHAR(128),
    CatalogNumber   VARCHAR(64),
    Reissue         CHAR(1) DEFAULT 'N',
    Mode            CHAR(1) DEFAULT 'S',
    DBX             CHAR(1) DEFAULT 'N'
);

CREATE INDEX idx_year_artist ON ArtistCatalog (Year, ArtistLast);

