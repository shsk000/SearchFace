-- SQLite Database Schema for SearchFace Application
-- This file contains the schema for local SQLite database (face_database.db)
-- Used for face recognition core data requiring high-speed access

-- =============================================================================
-- TABLES
-- =============================================================================

-- persons table (人物情報テーブル)
CREATE TABLE IF NOT EXISTS persons (
    person_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    base_image_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT
);

-- face_images table (顔画像情報テーブル)
CREATE TABLE IF NOT EXISTS face_images (
    image_id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id INTEGER NOT NULL,
    image_path TEXT NOT NULL,
    image_hash TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT,
    FOREIGN KEY (person_id) REFERENCES persons(person_id) ON DELETE CASCADE
);

-- face_indexes table (FAISSインデックス情報テーブル)
CREATE TABLE IF NOT EXISTS face_indexes (
    index_id INTEGER PRIMARY KEY AUTOINCREMENT,
    image_id INTEGER NOT NULL,
    index_position INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (image_id) REFERENCES face_images(image_id) ON DELETE CASCADE,
    UNIQUE(image_id, index_position)
);

-- =============================================================================
-- INDEXES
-- =============================================================================

-- Search optimization indexes
CREATE INDEX IF NOT EXISTS idx_persons_name ON persons(name);
CREATE INDEX IF NOT EXISTS idx_face_images_person_id ON face_images(person_id);
CREATE INDEX IF NOT EXISTS idx_face_indexes_image_id ON face_indexes(image_id);
CREATE INDEX IF NOT EXISTS idx_face_indexes_position ON face_indexes(index_position);

-- Unique constraint for index_position (ensures FAISS index consistency)
CREATE UNIQUE INDEX IF NOT EXISTS idx_face_indexes_position_unique ON face_indexes(index_position);

-- Note: face_images.image_hash has UNIQUE constraint, so additional index is not needed