import sqlite3
from typing import Dict, Any, List, Optional

def create_connection(db_file: str) -> sqlite3.Connection:
    """
    データベース接続を作成する
    
    Args:
        db_file (str): データベースファイルのパス
        
    Returns:
        sqlite3.Connection: データベース接続
    """
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    return conn

def init_database(conn: sqlite3.Connection) -> None:
    """
    データベースを初期化する
    
    Args:
        conn (sqlite3.Connection): データベース接続
    """
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS faces (
            face_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            image_path TEXT NOT NULL,
            index_position INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT
        )
    ''')
    conn.commit()

def get_face_by_name(conn: sqlite3.Connection, name: str) -> Optional[Dict[str, Any]]:
    """
    名前で顔データを検索する
    
    Args:
        conn (sqlite3.Connection): データベース接続
        name (str): 検索する名前
        
    Returns:
        Optional[Dict[str, Any]]: 顔データ。見つからない場合はNone
    """
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM faces WHERE name = ?', (name,))
    row = cursor.fetchone()
    return dict(row) if row else None

def get_face_by_index_position(conn: sqlite3.Connection, index_position: int) -> Optional[Dict[str, Any]]:
    """
    インデックス位置で顔データを検索する
    
    Args:
        conn (sqlite3.Connection): データベース接続
        index_position (int): インデックス位置
        
    Returns:
        Optional[Dict[str, Any]]: 顔データ。見つからない場合はNone
    """
    print(f"インデックス位置で検索: {index_position}")
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM faces WHERE index_position = ?', (index_position,))
    row = cursor.fetchone()
    if row:
        print(f"データが見つかりました: {dict(row)}")
    else:
        print("データが見つかりませんでした")
    return dict(row) if row else None

def insert_face(conn: sqlite3.Connection, name: str, image_path: str, index_position: int, metadata: str = None) -> int:
    """
    顔データを挿入する
    
    Args:
        conn (sqlite3.Connection): データベース接続
        name (str): 名前
        image_path (str): 画像パス
        index_position (int): インデックス位置
        metadata (str, optional): メタデータ
        
    Returns:
        int: 挿入された顔データのID
    """
    print(f"顔データを挿入: 名前={name}, インデックス位置={index_position}")
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO faces (name, image_path, index_position, metadata)
        VALUES (?, ?, ?, ?)
    ''', (name, image_path, index_position, metadata))
    conn.commit()
    return cursor.lastrowid

def get_all_faces(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """
    すべての顔データを取得する
    
    Args:
        conn (sqlite3.Connection): データベース接続
        
    Returns:
        List[Dict[str, Any]]: 顔データのリスト
    """
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM faces')
    rows = cursor.fetchall()
    return [{
        'face_id': row[0],
        'name': row[1],
        'image_path': row[2],
        'index_position': row[3],
        'created_at': row[4],
        'metadata': row[5]
    } for row in rows] 