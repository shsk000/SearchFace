# /api/search: 複数顔検出時のエラー対応

Date: 2024-06-13
Status: Open

## Request
現状、複数の顔がある画像を引数に `/api/search` API を実行すると、一つの顔に絞って類似検索を行うが、これをエラーにするように調整する。

## Objective
- 画像内に2つ以上の顔が検出された場合、APIはエラー（例: 400 Bad Request）を返す
- エラーメッセージは「複数の顔が検出されました。1枚の画像には1つの顔のみ許可されています。」等、わかりやすい内容にする
- 既存の単一顔画像の挙動は変更しない

## Action Plan
- [x] `/api/search` の顔検出部分で顔数を判定し、2つ以上ならエラーを返す処理を追加
  - get_face_encoding_from_arrayで複数顔検出時にImageValidationException(ErrorCode.MULTIPLE_FACES)をraiseするよう修正
  - /api/searchで例外をcatchし、エラーコード・メッセージを返す
- [x] ドキュメント・エラーメッセージの明確化
  - バックエンドのエラーメッセージは「画像に複数の顔が検出されました」
  - フロントエンドのエラーメッセージは「画像には1つの顔のみ含める必要があります」
- [x] フロントエンドで該当エラーのメッセージをtoastで表示する
  - 既存のtoast表示処理でMULTIPLE_FACESエラー時も適切に表示されることを確認

## Execution Log
