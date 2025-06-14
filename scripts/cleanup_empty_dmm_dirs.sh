#!/bin/bash
# 空のディレクトリを削除するスクリプト
# data/images/dmm 配下の空ディレクトリを検索・削除

set -euo pipefail

# ディレクトリパス
DMM_DIR="/home/shsk/git/SearchFace/data/images/dmm"

# 色付きログ用の関数
log_info() {
    echo -e "\033[32m[INFO]\033[0m $1"
}

log_warning() {
    echo -e "\033[33m[WARNING]\033[0m $1"
}

log_error() {
    echo -e "\033[31m[ERROR]\033[0m $1"
}

# メイン処理
main() {
    log_info "空ディレクトリクリーンアップスクリプト開始"
    
    # ディレクトリ存在チェック
    if [[ ! -d "$DMM_DIR" ]]; then
        log_error "ディレクトリが存在しません: $DMM_DIR"
        exit 1
    fi
    
    log_info "対象ディレクトリ: $DMM_DIR"
    
    # 空ディレクトリを検索
    log_info "空ディレクトリを検索中..."
    
    # find コマンドで空ディレクトリを検索
    # -type d: ディレクトリのみ
    # -empty: 空のディレクトリ
    # -mindepth 1: 検索対象ディレクトリ自体は除外
    EMPTY_DIRS=$(find "$DMM_DIR" -mindepth 1 -type d -empty)
    
    if [[ -z "$EMPTY_DIRS" ]]; then
        log_info "空ディレクトリは見つかりませんでした"
        exit 0
    fi
    
    # 見つかった空ディレクトリの数をカウント
    EMPTY_COUNT=$(echo "$EMPTY_DIRS" | wc -l)
    log_warning "空ディレクトリが ${EMPTY_COUNT} 個見つかりました:"
    
    # 空ディレクトリリストを表示
    echo "$EMPTY_DIRS" | while IFS= read -r dir; do
        echo "  - $(basename "$dir")"
    done
    
    # 削除確認
    echo
    read -p "これらの空ディレクトリを削除しますか? (y/N): " -r
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "キャンセルされました"
        exit 0
    fi
    
    # 削除実行
    log_info "空ディレクトリを削除中..."
    
    DELETED_COUNT=0
    ERROR_COUNT=0
    
    echo "$EMPTY_DIRS" | while IFS= read -r dir; do
        if rmdir "$dir" 2>/dev/null; then
            echo "✅ 削除成功: $(basename "$dir")"
            ((DELETED_COUNT++)) || true
        else
            echo "❌ 削除失敗: $(basename "$dir")"
            ((ERROR_COUNT++)) || true
        fi
    done
    
    # 結果表示
    echo
    log_info "処理完了"
    log_info "削除成功: ${DELETED_COUNT} 個"
    
    if [[ $ERROR_COUNT -gt 0 ]]; then
        log_warning "削除失敗: ${ERROR_COUNT} 個"
    fi
    
    # 最終確認（再度空ディレクトリをチェック）
    REMAINING_EMPTY=$(find "$DMM_DIR" -mindepth 1 -type d -empty | wc -l)
    if [[ $REMAINING_EMPTY -eq 0 ]]; then
        log_info "すべての空ディレクトリが削除されました"
    else
        log_warning "まだ ${REMAINING_EMPTY} 個の空ディレクトリが残っています"
    fi
}

# ヘルプ表示
show_help() {
    cat << EOF
使用方法: $0 [オプション]

空ディレクトリクリーンアップスクリプト
data/images/dmm 配下の空ディレクトリを検索・削除します。

オプション:
  -h, --help     このヘルプを表示
  -f, --force    確認なしで削除実行（危険）
  -d, --dry-run  削除せずに空ディレクトリを表示のみ

例:
  $0              # 対話的に削除
  $0 --dry-run    # 空ディレクトリを表示のみ
  $0 --force      # 確認なしで削除
EOF
}

# ドライラン実行
dry_run() {
    log_info "ドライラン実行 - 実際の削除は行いません"
    
    if [[ ! -d "$DMM_DIR" ]]; then
        log_error "ディレクトリが存在しません: $DMM_DIR"
        exit 1
    fi
    
    EMPTY_DIRS=$(find "$DMM_DIR" -mindepth 1 -type d -empty)
    
    if [[ -z "$EMPTY_DIRS" ]]; then
        log_info "空ディレクトリは見つかりませんでした"
        exit 0
    fi
    
    EMPTY_COUNT=$(echo "$EMPTY_DIRS" | wc -l)
    log_info "空ディレクトリが ${EMPTY_COUNT} 個見つかりました:"
    
    echo "$EMPTY_DIRS" | while IFS= read -r dir; do
        echo "  - $(basename "$dir")"
    done
}

# 強制削除実行
force_delete() {
    log_warning "強制削除モード - 確認なしで削除を実行します"
    
    if [[ ! -d "$DMM_DIR" ]]; then
        log_error "ディレクトリが存在しません: $DMM_DIR"
        exit 1
    fi
    
    EMPTY_DIRS=$(find "$DMM_DIR" -mindepth 1 -type d -empty)
    
    if [[ -z "$EMPTY_DIRS" ]]; then
        log_info "空ディレクトリは見つかりませんでした"
        exit 0
    fi
    
    EMPTY_COUNT=$(echo "$EMPTY_DIRS" | wc -l)
    log_info "空ディレクトリ ${EMPTY_COUNT} 個を削除中..."
    
    DELETED_COUNT=0
    ERROR_COUNT=0
    
    echo "$EMPTY_DIRS" | while IFS= read -r dir; do
        if rmdir "$dir" 2>/dev/null; then
            echo "✅ 削除: $(basename "$dir")"
            ((DELETED_COUNT++)) || true
        else
            echo "❌ 失敗: $(basename "$dir")"
            ((ERROR_COUNT++)) || true
        fi
    done
    
    log_info "処理完了 - 削除: ${DELETED_COUNT} 個, 失敗: ${ERROR_COUNT} 個"
}

# オプション解析
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    -d|--dry-run)
        dry_run
        exit 0
        ;;
    -f|--force)
        force_delete
        exit 0
        ;;
    "")
        main
        ;;
    *)
        log_error "不明なオプション: $1"
        echo "ヘルプを表示: $0 --help"
        exit 1
        ;;
esac