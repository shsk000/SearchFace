#!/usr/bin/env python3
"""
FAISSインデックスの復旧スクリプト

既存のface_imagesテーブルのデータからFAISSインデックスを再構築します。
直列処理で安定性を重視した設計です。
"""

import argparse
import gc
import logging
import os
import sys
import time
from typing import List, Dict, Any, Optional, Tuple

import faiss
import numpy as np

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.database.face_index_database import FaceIndexDatabase
from src.face import face_utils
from src.utils import log_utils

# ロガーの設定
logger = log_utils.get_logger(__name__)

class FAISSIndexRebuilder:
    """FAISSインデックスの復旧クラス"""
    
    def __init__(self, db_path: Optional[str] = None, index_path: Optional[str] = None):
        """
        Args:
            db_path (Optional[str]): データベースファイルのパス（テスト用）
            index_path (Optional[str]): FAISSインデックスファイルのパス（テスト用）
        """
        self.db_path = db_path
        self.index_path = index_path or "data/face.index"
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'error_details': []
        }
        self.encodings = []
        self.face_metadata = []
        
    def _update_stats(self, stat_type: str, error_detail: Optional[Dict[str, Any]] = None):
        """統計更新"""
        self.stats[stat_type] += 1
        if error_detail and stat_type == 'failed':
            self.stats['error_details'].append(error_detail)
    
    def _process_batch(self, face_data_list: List[Dict[str, Any]]):
        """バッチを直列処理
        
        Args:
            face_data_list (List[Dict[str, Any]]): 処理対象の顔データリスト
        """
        logger.info(f"直列処理開始: {len(face_data_list)}件")
        
        for face_data in face_data_list:
            try:
                encoding, metadata = self._process_single_face(face_data)
                if encoding is not None and metadata:
                    self.encodings.append(encoding)
                    self.face_metadata.append(metadata)
            except Exception as e:
                logger.error(f"処理中にエラーが発生: {face_data['image_path']} - {str(e)}")
                self._update_stats('failed', {
                    'image_id': face_data['image_id'],
                    'image_path': face_data['image_path'],
                    'error': f'処理エラー: {str(e)}'
                })
    
    def _process_single_face(self, face_data: Dict[str, Any]) -> Tuple[Optional[np.ndarray], Dict[str, Any]]:
        """単一の顔データを処理
        
        Args:
            face_data (Dict[str, Any]): 顔データ情報
            
        Returns:
            Tuple[Optional[np.ndarray], Dict[str, Any]]: エンコーディングとメタデータ
        """
        image_path = face_data['image_path']
        index_position = face_data['index_position']
        
        try:
            logger.debug(f"エンコーディング取得中: {image_path} (index_position: {index_position})")
            encoding = face_utils.get_face_encoding(image_path)
            
            if encoding is not None:
                self._update_stats('success')
                metadata = {
                    'image_id': face_data['image_id'],
                    'person_id': face_data['person_id'],
                    'image_path': image_path,
                    'index_position': index_position
                }
                return encoding, metadata
            else:
                logger.warning(f"エンコーディングの取得に失敗: {image_path}")
                self._update_stats('failed', {
                    'image_id': face_data['image_id'],
                    'image_path': image_path,
                    'error': 'エンコーディングの取得に失敗'
                })
                return None, {}
                
        except Exception as e:
            logger.error(f"エンコーディング取得でエラー: {image_path} - {str(e)}")
            self._update_stats('failed', {
                'image_id': face_data['image_id'],
                'image_path': image_path,
                'error': f'例外エラー: {str(e)}'
            })
            return None, {}
    
    def rebuild_index(self, batch_size: int = 100, resume_from: Optional[int] = None) -> Dict[str, Any]:
        """FAISSインデックスを正しいindex_positionで再構築
        
        Args:
            batch_size (int): バッチサイズ
            resume_from (Optional[int]): 続行開始位置（index_position）
            
        Returns:
            Dict[str, Any]: 処理結果の統計情報
        """
        start_time = time.time()
        
        # データベースから顔データを取得（直接SQLite接続を使用）
        logger.info("データベースから顔データを取得中...")
        import sqlite3
        db_path = self.db_path or "data/face_database.db"
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 全データを取得してindex_positionでソート
        cursor.execute("""
            SELECT fi.image_id, fi.person_id, fi.image_path, fxi.index_position
            FROM face_images fi
            JOIN face_indexes fxi ON fi.image_id = fxi.image_id
            ORDER BY fxi.index_position
        """)
        
        all_face_data = cursor.fetchall()
        total_count = len(all_face_data)
        self.stats['total'] = total_count
        
        logger.info(f"復旧対象: {total_count}件の顔データ")
        
        if total_count == 0:
            logger.warning("復旧対象のデータがありません")
            conn.close()
            return self.stats
        
        # 最大index_positionを取得してFAISSインデックスのサイズを決定
        max_index_position = max(row['index_position'] for row in all_face_data)
        logger.info(f"最大index_position: {max_index_position}")
        
        # FAISSインデックスを初期化
        index = faiss.IndexFlatL2(128)  # face_recognitionは128次元
        logger.info("新しいインデックスを作成")
        
        # 位置別のベクトル配列を準備（max_index_position + 1のサイズ）
        vectors = np.zeros((max_index_position + 1, 128), dtype=np.float32)
        position_filled = np.zeros(max_index_position + 1, dtype=bool)
        
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        
        # バッチ処理で段階的にエンコーディングを取得
        offset = 0
        while offset < total_count:
            current_batch_size = min(batch_size, total_count - offset)
            batch_data = [dict(row) for row in all_face_data[offset:offset + current_batch_size]]
            
            logger.info(f"バッチ処理中... ({offset + 1}-{offset + len(batch_data)}/{total_count})")
            
            # 直列処理でエンコーディングを取得
            for face_data in batch_data:
                try:
                    image_path = face_data['image_path']
                    index_position = face_data['index_position']
                    
                    encoding = face_utils.get_face_encoding(image_path)
                    
                    if encoding is not None:
                        # 指定されたindex_positionに正確に配置
                        vectors[index_position] = encoding
                        position_filled[index_position] = True
                        self._update_stats('success')
                    else:
                        logger.warning(f"エンコーディングの取得に失敗: {image_path}")
                        self._update_stats('failed', {
                            'image_id': face_data['image_id'],
                            'image_path': image_path,
                            'error': 'エンコーディングの取得に失敗'
                        })
                        
                except Exception as e:
                    logger.error(f"エンコーディング取得でエラー: {face_data['image_path']} - {str(e)}")
                    self._update_stats('failed', {
                        'image_id': face_data['image_id'],
                        'image_path': face_data['image_path'],
                        'error': f'例外エラー: {str(e)}'
                    })
            
            offset += len(batch_data)
            
            # 定期的に中間保存（1000件ごと）- 速度重視の場合はコメントアウト
            # if offset % 1000 == 0:
            #     logger.info(f"中間保存中... ({offset}件処理済み)")
            #     self._save_intermediate_index(vectors, position_filled, max_index_position)
            
            # メモリクリーンアップ（一定間隔で実行）
            if offset % (batch_size * 10) == 0:  # 頻度を下げる（5→10）
                gc.collect()
                logger.debug(f"メモリクリーンアップを実行: {offset}件処理済み")
            
            # 進捗表示
            elapsed_time = time.time() - start_time
            if elapsed_time > 0:
                rate = offset / elapsed_time
                remaining_time = (total_count - offset) / rate if rate > 0 else 0
                logger.info(f"進捗: {offset}/{total_count} ({offset/total_count*100:.1f}%) - "
                          f"処理速度: {rate:.2f}件/秒 - 残り時間: {remaining_time:.0f}秒")
        
        # 有効なベクトルのみをFAISSインデックスに追加（順序を保持）
        logger.info("FAISSインデックスにベクトルを追加中...")
        valid_vectors = []
        valid_positions = []
        
        for pos in range(max_index_position + 1):
            if position_filled[pos]:
                valid_vectors.append(vectors[pos])
                valid_positions.append(pos)
        
        if valid_vectors:
            # 全ベクトルを一度に追加（順序が重要）
            all_vectors = np.array(valid_vectors, dtype=np.float32)
            
            # 位置合わせのため、不足分を0ベクトルで埋める
            final_vectors = np.zeros((max_index_position + 1, 128), dtype=np.float32)
            for i, pos in enumerate(valid_positions):
                final_vectors[pos] = all_vectors[i]
            
            # FAISSに全ベクトルを追加（0ベクトル含む）
            index.add(final_vectors)
            
            logger.info(f"FAISSインデックス構築完了: {index.ntotal}ベクトル")
            logger.info(f"有効ベクトル数: {len(valid_vectors)} / {max_index_position + 1}")
        
        # インデックスファイルを保存
        faiss.write_index(index, self.index_path)
        
        # 最終確認とログ出力
        logger.info("FAISSインデックスの構築が完了しました")
        if os.path.exists(self.index_path):
            file_size = os.path.getsize(self.index_path)
            logger.info(f"最終インデックスファイル: {self.index_path}")
            logger.info(f"最終インデックス内ベクトル数: {index.ntotal}")
            logger.info(f"最終ファイルサイズ: {file_size:,} バイト")
        else:
            logger.error(f"インデックスファイルの保存に失敗: {self.index_path}")
            
        logger.info(f"処理成功: {self.stats['success']}件")
        logger.info(f"処理失敗: {self.stats['failed']}件")
        
        # 統計情報の更新
        total_time = time.time() - start_time
        self.stats['total_time'] = total_time
        
        conn.close()
        return self.stats
    
    def _save_intermediate_index(self, vectors: np.ndarray, position_filled: np.ndarray, max_index_position: int):
        """中間状態でのFAISSインデックス保存"""
        try:
            # 現在までの有効なベクトルをFAISSインデックスに追加
            temp_index = faiss.IndexFlatL2(128)
            
            # 位置合わせのため、全てのpositionを含む配列を作成
            final_vectors = np.zeros((max_index_position + 1, 128), dtype=np.float32)
            valid_count = 0
            
            for pos in range(max_index_position + 1):
                if position_filled[pos]:
                    final_vectors[pos] = vectors[pos]
                    valid_count += 1
            
            # FAISSに追加
            temp_index.add(final_vectors)
            
            # 中間ファイルとして保存
            intermediate_path = self.index_path + ".tmp"
            faiss.write_index(temp_index, intermediate_path)
            
            logger.info(f"中間保存完了: {valid_count}件のベクトル, ファイル: {intermediate_path}")
            
        except Exception as e:
            logger.warning(f"中間保存でエラー: {str(e)}")  # エラーでも処理は続行
    
    def print_stats(self):
        """処理結果の統計情報を表示"""
        print("\n=== FAISSインデックス復旧結果 ===")
        print(f"総処理件数: {self.stats['total']}")
        print(f"成功: {self.stats['success']}")
        print(f"失敗: {self.stats['failed']}")
        
        if 'total_time' in self.stats:
            print(f"処理時間: {self.stats['total_time']:.2f}秒")
            if self.stats['total_time'] > 0:
                print(f"処理速度: {self.stats['total']/self.stats['total_time']:.2f}件/秒")
        
        # エラー詳細
        if self.stats['error_details']:
            print(f"\n=== エラー詳細 (最初の10件) ===")
            for i, error in enumerate(self.stats['error_details'][:10]):
                print(f"{i+1}. image_id: {error['image_id']}")
                print(f"   パス: {error['image_path']}")
                print(f"   エラー: {error['error']}")


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='FAISSインデックスの復旧')
    parser.add_argument('--batch-size', type=int, default=100, help='バッチサイズ（デフォルト: 100）')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='詳細ログを出力')
    parser.add_argument('--resume-from', type=int, 
                       help='指定したindex_position以降から処理を再開')
    
    args = parser.parse_args()
    
    # ログレベル設定
    if args.verbose:
        log_utils.setup_logging(level=logging.DEBUG)
    else:
        log_utils.setup_logging(level=logging.INFO)
    
    rebuilder = FAISSIndexRebuilder()
    
    try:
        logger.info("FAISSインデックスの復旧を開始します")
        logger.info(f"処理設定: バッチサイズ={args.batch_size} (直列処理)")
        
        # インデックス復旧実行
        rebuilder.rebuild_index(
            batch_size=args.batch_size,
            resume_from=args.resume_from
        )
        
        # 結果表示
        rebuilder.print_stats()
        
        # 復旧後のインデックス確認
        if os.path.exists(rebuilder.index_path):
            face_db = FaceIndexDatabase()
            index_stats = face_db.get_index_stats()
            print(f"\n=== 復旧後のインデックス統計 ===")
            print(f"FAISSベクトル数: {index_stats['faiss_vector_count']}")
            print(f"DB画像数: {index_stats['db_image_count']}")
            print(f"DBインデックス数: {index_stats['db_index_count']}")
            face_db.close()
        
    except KeyboardInterrupt:
        logger.info("処理が中断されました")
        rebuilder.print_stats()
    except Exception as e:
        logger.error(f"処理中にエラーが発生しました: {str(e)}")
        raise


if __name__ == "__main__":
    main()