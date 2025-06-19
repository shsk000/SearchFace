-- SQLite Database Schema for SearchFace Application
-- This file contains the schema for local SQLite database (face_database.db)
-- Used for face recognition core data requiring high-speed access
-- 
-- IMPORTANT: This schema matches the PersonDatabase implementation exactly
-- Updated to resolve test/production schema inconsistencies

-- =============================================================================
-- TABLES
-- =============================================================================

-- persons table (人物情報テーブル)
-- Updated to match current PersonDatabase implementation
CREATE TABLE IF NOT EXISTS persons (
    person_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    dmm_actress_id INTEGER UNIQUE,
    base_image_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT
);

-- person_profiles table (人物プロフィールテーブル - PersonDatabase実装に完全対応)
CREATE TABLE IF NOT EXISTS person_profiles (
    profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id INTEGER NOT NULL UNIQUE,
    
    -- 基本情報
    ruby TEXT,
    birthday DATE,
    birth_year INTEGER,
    blood_type TEXT,
    hobby TEXT,
    prefectures TEXT,
    
    -- 身体情報
    height INTEGER,
    bust INTEGER,
    waist INTEGER,
    hip INTEGER,
    cup TEXT,
    
    -- 画像URL
    image_small_url TEXT,
    image_large_url TEXT,
    
    -- DMM情報
    dmm_list_url_digital TEXT,
    dmm_list_url_monthly_premium TEXT,
    dmm_list_url_mono TEXT,
    
    -- システム情報
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 追加メタデータ（柔軟性のため残す）
    metadata TEXT,
    
    FOREIGN KEY (person_id) REFERENCES persons(person_id) ON DELETE CASCADE
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
CREATE INDEX IF NOT EXISTS idx_persons_dmm_actress_id ON persons(dmm_actress_id);
CREATE INDEX IF NOT EXISTS idx_person_profiles_person_id ON person_profiles(person_id);

-- Profile search indexes (body measurements focused)
CREATE INDEX IF NOT EXISTS idx_profiles_ruby ON person_profiles(ruby);
CREATE INDEX IF NOT EXISTS idx_profiles_height ON person_profiles(height);
CREATE INDEX IF NOT EXISTS idx_profiles_bust ON person_profiles(bust);
CREATE INDEX IF NOT EXISTS idx_profiles_cup ON person_profiles(cup);

-- Composite index for body measurements filtering
CREATE INDEX IF NOT EXISTS idx_profiles_measurements ON person_profiles(height, cup, bust);

-- Face images and indexes
CREATE INDEX IF NOT EXISTS idx_face_images_person_id ON face_images(person_id);
CREATE INDEX IF NOT EXISTS idx_face_indexes_image_id ON face_indexes(image_id);
CREATE INDEX IF NOT EXISTS idx_face_indexes_position ON face_indexes(index_position);

-- Unique constraint for index_position (ensures FAISS index consistency)
CREATE UNIQUE INDEX IF NOT EXISTS idx_face_indexes_position_unique ON face_indexes(index_position);

-- Note: face_images.image_hash has UNIQUE constraint, so additional index is not needed