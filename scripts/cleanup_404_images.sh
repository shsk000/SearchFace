#!/bin/bash
# 404エラー画像（小さいファイル）を削除するスクリプト
# data/images/dmm/*/products/ 配下の5KB以下のproduct-*.jpgファイルを削除

set -euo pipefail

# 設定
DMM_DIR="/home/shsk/git/SearchFace/data/images/dmm"
MAX_SIZE="5k"  # 5KB以下のファイルを削除対象
FILE_PATTERN="product-*.jpg"

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

# ファイルサイズを人間が読みやすい形式で表示
format_size() {
    local size=$1
    if [ "$size" -lt 1024 ]; then
        echo "${size}B"
    elif [ "$size" -lt 1048576 ]; then
        echo "$((size / 1024))KB"
    else
        echo "$((size / 1048576))MB"
    fi
}

# メイン処理
main() {
    log_info "404エラー画像クリーンアップスクリプト開始"
    
    # ディレクトリ存在チェック
    if [ ! -d "$DMM_DIR" ]; then
        log_error "ディレクトリが存在しません: $DMM_DIR"
        exit 1
    fi
    
    log_info "対象ディレクトリ: $DMM_DIR"
    log_info "削除対象: ${MAX_SIZE}以下の${FILE_PATTERN}ファイル"
    
    # 小さいファイルを検索
    log_info "小さいファイルを検索中..."
    
    # 一時ファイルを使用してファイルリストを保存
    TEMP_FILE=$(mktemp)
    find "$DMM_DIR" -path "*/products/*" -name "$FILE_PATTERN" -size "-${MAX_SIZE}" -type f > "$TEMP_FILE" 2>/dev/null || true
    
    if [ ! -s "$TEMP_FILE" ]; then
        log_info "削除対象のファイルは見つかりませんでした"
        rm -f "$TEMP_FILE"
        exit 0
    fi
    
    # 見つかったファイルの数をカウント
    FILE_COUNT=$(wc -l < "$TEMP_FILE")
    log_warning "${FILE_COUNT} 個の小さいファイルが見つかりました:"
    
    # ファイルリストを表示（サイズ付き）
    while IFS= read -r file; do
        if [ -f "$file" ]; then
            # macOSとLinuxの両方に対応
            if command -v stat >/dev/null 2>&1; then
                size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo "0")
            else
                size="0"
            fi
            
            actress_name=$(basename "$(dirname "$(dirname "$file")")")
            filename=$(basename "$file")
            
            if [ "$size" != "0" ] && [ "$size" != "unknown" ]; then
                formatted_size=$(format_size "$size")
                echo "  - $actress_name/$filename (${formatted_size})"
            else
                echo "  - $actress_name/$filename (サイズ不明)"
            fi
        fi
    done < "$TEMP_FILE"
    
    # 削除確認
    echo
    read -p "これらの小さいファイル（404エラー画像の可能性大）を削除しますか? (y/N): " -r
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "キャンセルされました"
        rm -f "$TEMP_FILE"
        exit 0
    fi
    
    # 削除実行
    log_info "小さいファイルを削除中..."
    
    DELETED_COUNT=0
    ERROR_COUNT=0
    TOTAL_SIZE=0
    
    while IFS= read -r file; do
        if [ -f "$file" ]; then
            # ファイルサイズ取得
            if command -v stat >/dev/null 2>&1; then
                size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo "0")
            else
                size="0"
            fi
            
            actress_name=$(basename "$(dirname "$(dirname "$file")")")
            filename=$(basename "$file")
            
            if rm "$file" 2>/dev/null; then
                echo "✅ 削除成功: $actress_name/$filename"
                DELETED_COUNT=$((DELETED_COUNT + 1))
                if [ "$size" != "0" ]; then
                    TOTAL_SIZE=$((TOTAL_SIZE + size))
                fi
            else
                echo "❌ 削除失敗: $actress_name/$filename"
                ERROR_COUNT=$((ERROR_COUNT + 1))
            fi
        fi
    done < "$TEMP_FILE"
    
    # 一時ファイル削除
    rm -f "$TEMP_FILE"
    
    # 結果表示
    echo
    log_info "処理完了"
    log_info "削除成功: ${DELETED_COUNT} 個"
    
    if [ "$TOTAL_SIZE" -gt 0 ]; then
        formatted_total=$(format_size "$TOTAL_SIZE")
        log_info "削除容量: ${formatted_total}"
    fi
    
    if [ "$ERROR_COUNT" -gt 0 ]; then
        log_warning "削除失敗: ${ERROR_COUNT} 個"
    fi
    
    # 最終確認（再度小さいファイルをチェック）
    REMAINING_COUNT=$(find "$DMM_DIR" -path "*/products/*" -name "$FILE_PATTERN" -size "-${MAX_SIZE}" -type f 2>/dev/null | wc -l || echo "0")
    if [ "$REMAINING_COUNT" -eq 0 ]; then
        log_info "すべての小さいファイルが削除されました"
    else
        log_warning "まだ ${REMAINING_COUNT} 個の小さいファイルが残っています"
    fi
}

# ドライラン実行
dry_run() {
    log_info "ドライラン実行 - 実際の削除は行いません"
    
    if [ ! -d "$DMM_DIR" ]; then
        log_error "ディレクトリが存在しません: $DMM_DIR"
        exit 1
    fi
    
    log_info "削除対象: ${MAX_SIZE}以下の${FILE_PATTERN}ファイル"
    
    # 一時ファイルを使用
    TEMP_FILE=$(mktemp)
    find "$DMM_DIR" -path "*/products/*" -name "$FILE_PATTERN" -size "-${MAX_SIZE}" -type f > "$TEMP_FILE" 2>/dev/null || true
    
    if [ ! -s "$TEMP_FILE" ]; then
        log_info "削除対象のファイルは見つかりませんでした"
        rm -f "$TEMP_FILE"
        exit 0
    fi
    
    FILE_COUNT=$(wc -l < "$TEMP_FILE")
    log_info "${FILE_COUNT} 個の削除対象ファイルが見つかりました:"
    
    TOTAL_SIZE=0
    while IFS= read -r file; do
        if [ -f "$file" ]; then
            if command -v stat >/dev/null 2>&1; then
                size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo "0")
            else
                size="0"
            fi
            
            actress_name=$(basename "$(dirname "$(dirname "$file")")")
            filename=$(basename "$file")
            
            if [ "$size" != "0" ]; then
                formatted_size=$(format_size "$size")
                echo "  - $actress_name/$filename (${formatted_size})"
                TOTAL_SIZE=$((TOTAL_SIZE + size))
            else
                echo "  - $actress_name/$filename (サイズ不明)"
            fi
        fi
    done < "$TEMP_FILE"
    
    rm -f "$TEMP_FILE"
    
    if [ "$TOTAL_SIZE" -gt 0 ]; then
        formatted_total=$(format_size "$TOTAL_SIZE")
        log_info "削除予定容量: ${formatted_total}"
    fi
}

# 強制削除実行
force_delete() {
    log_warning "強制削除モード - 確認なしで削除を実行します"
    
    if [ ! -d "$DMM_DIR" ]; then
        log_error "ディレクトリが存在しません: $DMM_DIR"
        exit 1
    fi
    
    # 一時ファイルを使用
    TEMP_FILE=$(mktemp)
    find "$DMM_DIR" -path "*/products/*" -name "$FILE_PATTERN" -size "-${MAX_SIZE}" -type f > "$TEMP_FILE" 2>/dev/null || true
    
    if [ ! -s "$TEMP_FILE" ]; then
        log_info "削除対象のファイルは見つかりませんでした"
        rm -f "$TEMP_FILE"
        exit 0
    fi
    
    FILE_COUNT=$(wc -l < "$TEMP_FILE")
    log_info "小さいファイル ${FILE_COUNT} 個を削除中..."
    
    DELETED_COUNT=0
    ERROR_COUNT=0
    TOTAL_SIZE=0
    
    while IFS= read -r file; do
        if [ -f "$file" ]; then
            if command -v stat >/dev/null 2>&1; then
                size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo "0")
            else
                size="0"
            fi
            
            actress_name=$(basename "$(dirname "$(dirname "$file")")")
            filename=$(basename "$file")
            
            if rm "$file" 2>/dev/null; then
                echo "✅ 削除: $actress_name/$filename"
                DELETED_COUNT=$((DELETED_COUNT + 1))
                if [ "$size" != "0" ]; then
                    TOTAL_SIZE=$((TOTAL_SIZE + size))
                fi
            else
                echo "❌ 失敗: $actress_name/$filename"
                ERROR_COUNT=$((ERROR_COUNT + 1))
            fi
        fi
    done < "$TEMP_FILE"
    
    rm -f "$TEMP_FILE"
    
    if [ "$TOTAL_SIZE" -gt 0 ]; then
        formatted_total=$(format_size "$TOTAL_SIZE")
        log_info "処理完了 - 削除: ${DELETED_COUNT} 個, 失敗: ${ERROR_COUNT} 個, 容量: ${formatted_total}"
    else
        log_info "処理完了 - 削除: ${DELETED_COUNT} 個, 失敗: ${ERROR_COUNT} 個"
    fi
}

# ヘルプ表示
show_help() {
    cat << EOF
使用方法: $0 [オプション]

404エラー画像クリーンアップスクリプト
data/images/dmm/*/products/ 配下の小さい（5KB以下）product-*.jpgファイルを削除します。

オプション:
  -h, --help      このヘルプを表示
  -s, --size SIZE 削除対象サイズを指定（デフォルト: 5k）
  -f, --force     確認なしで削除実行（危険）
  -d, --dry-run   削除せずにファイルを表示のみ

例:
  $0              # 対話的に削除（5KB以下）
  $0 --size 3k    # 3KB以下のファイルを削除
  $0 --dry-run    # 削除対象ファイルを表示のみ
  $0 --force      # 確認なしで削除
EOF
}

# オプション解析
while [ $# -gt 0 ]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -s|--size)
            MAX_SIZE="$2"
            shift 2
            ;;
        -d|--dry-run)
            dry_run
            exit 0
            ;;
        -f|--force)
            force_delete
            exit 0
            ;;
        *)
            log_error "不明なオプション: $1"
            echo "ヘルプを表示: $0 --help"
            exit 1
            ;;
    esac
done

# デフォルトの対話的実行
main