"""
Database testing utilities for safe test database creation and management.

CRITICAL SECURITY NOTE:
- These utilities ensure all tests use TEMPORARY files only
- NEVER access production data/ directory
- All database connections are isolated and auto-cleaned
"""

import sqlite3
import tempfile
import os
from typing import Tuple, Optional
from contextlib import contextmanager


def create_test_database_with_schema(schema_file: Optional[str] = None) -> Tuple[sqlite3.Connection, str]:
    """
    Create a temporary SQLite database with proper schema for testing.
    
    SAFETY: Uses tempfile to ensure no production database access.
    
    Args:
        schema_file: Optional path to schema file. If None, uses sqlite_schema.sql from project root (ensuring test/production consistency).
        
    Returns:
        Tuple of (connection, db_path) - connection is configured with Row factory
        
    Raises:
        FileNotFoundError: If schema_file is provided but doesn't exist
    """
    # Create temporary database file
    temp_fd, temp_path = tempfile.mkstemp(suffix='.db', prefix='test_face_db_')
    os.close(temp_fd)  # Close file descriptor, we'll use sqlite3 to open
    
    # Create connection with Row factory for dict-style access
    conn = sqlite3.connect(temp_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Determine schema file path
    if schema_file is None:
        # Use project's sqlite_schema.sql by default
        # Docker container paths (project root mounted at /app)
        possible_paths = [
            '/app/sqlite_schema.sql',  # Docker container path (project root)
            os.path.join(os.path.dirname(__file__), '..', '..', 'sqlite_schema.sql'),  # Project root relative
            os.path.join(os.getcwd(), 'sqlite_schema.sql')  # Current working directory
        ]
        
        schema_file = None
        for path in possible_paths:
            abs_path = os.path.abspath(path)
            if os.path.exists(abs_path):
                schema_file = abs_path
                break
        
        if schema_file is None:
            raise FileNotFoundError(f"Could not find sqlite_schema.sql in any of these locations: {possible_paths}")
    
    if os.path.exists(schema_file):
        # Read and execute schema file
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        cursor.executescript(schema_sql)
    else:
        raise FileNotFoundError(f"Schema file not found: {schema_file}")
    
    conn.commit()
    return conn, temp_path



@contextmanager
def isolated_test_database(schema_file: Optional[str] = None):
    """
    Context manager for safe test database creation and cleanup.
    
    SAFETY: Automatically cleans up temporary files.
    Uses project root sqlite_schema.sql to ensure consistency with implementation.
    
    Args:
        schema_file: Optional path to schema file. If None, uses project's sqlite_schema.sql
        
    Yields:
        Tuple of (connection, db_path)
        
    Example:
        with isolated_test_database() as (conn, db_path):
            cursor = conn.cursor()
            cursor.execute("INSERT INTO persons (name) VALUES (?)", ("Test Person",))
            conn.commit()
            # Database is automatically cleaned up
    """
    conn = None
    db_path = None
    
    try:
        conn, db_path = create_test_database_with_schema(schema_file)
        yield conn, db_path
    finally:
        if conn:
            conn.close()
        if db_path and os.path.exists(db_path):
            try:
                os.unlink(db_path)
            except OSError:
                pass  # File might be already deleted or locked


def create_test_person_data(conn: sqlite3.Connection, person_name: str = "Test Person", 
                          base_image_path: str = "/tmp/test_image.jpg") -> int:
    """
    Create test person data in the test database.
    
    SAFETY: Only works with test database connections.
    
    Args:
        conn: SQLite connection (should be test database)
        person_name: Name for test person
        base_image_path: SAFE test image path (should be /tmp/ or similar)
        
    Returns:
        person_id of created person
        
    Raises:
        ValueError: If base_image_path appears to be production path
    """
    if base_image_path.startswith('data/'):
        raise ValueError(f"SECURITY VIOLATION: base_image_path '{base_image_path}' "
                        f"appears to be production path. Use /tmp/ or similar for tests.")
    
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO persons (name, base_image_path) VALUES (?, ?)",
        (person_name, base_image_path)
    )
    conn.commit()
    return cursor.lastrowid