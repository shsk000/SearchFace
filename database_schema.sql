-- SearchFace Database Schema for Turso
-- This file contains table definitions for search history and ranking features
-- Run this SQL file in your Turso database before starting the application
--
-- IMPORTANT NOTES:
-- - Core face recognition tables (persons, face_images, face_indexes) are stored in LOCAL SQLite
-- - Search history and ranking tables are stored in Turso (cloud database)
-- - Foreign key constraints to persons table are NOT used due to cross-database limitations
-- - Data integrity between local SQLite and Turso must be maintained at application level

-- ========================================
-- Search History Tables
-- ========================================

-- 検索履歴テーブル（1回の検索で複数行記録）
-- Note: person_idはローカルSQLiteのpersonsテーブルを参照するが、異なるDB間のため外部キー制約は使用しない
CREATE TABLE IF NOT EXISTS search_history (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    search_session_id TEXT NOT NULL,
    result_rank INTEGER NOT NULL,
    person_id INTEGER NOT NULL,
    distance REAL NOT NULL,
    image_path TEXT NOT NULL,
    search_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT
);

-- ========================================
-- Ranking Tables
-- ========================================

-- 人物ランキングテーブル（集計データ）
-- Note: person_idはローカルSQLiteのpersonsテーブルを参照するが、異なるDB間のため外部キー制約は使用しない
CREATE TABLE IF NOT EXISTS person_ranking (
    ranking_id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id INTEGER NOT NULL UNIQUE,
    win_count INTEGER DEFAULT 0,
    last_win_timestamp TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- Indexes for Performance
-- ========================================

-- Search history indexes
CREATE INDEX IF NOT EXISTS idx_search_history_person_id ON search_history(person_id);
CREATE INDEX IF NOT EXISTS idx_search_history_timestamp ON search_history(search_timestamp);
CREATE INDEX IF NOT EXISTS idx_search_history_session_rank ON search_history(search_session_id, result_rank);

-- Ranking indexes
CREATE INDEX IF NOT EXISTS idx_person_ranking_person_id ON person_ranking(person_id);
CREATE INDEX IF NOT EXISTS idx_person_ranking_win_count ON person_ranking(win_count DESC);