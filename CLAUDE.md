# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project rules

**CRITICAL: 以下のルールは必須です。例外なく従ってください。**

### Task Management Rules (最重要)

1. **ユーザーからの指示を受けた際の必須プロセス:**
  - 命令を遂行する前に**必ず**`.cursor/rules/first.mdc`ファイルを読み込む
  - プロジェクトの詳細な設定は `.cursor/rules/project.mdc` を参照してください
  - Python開発に関する詳細な設定は `.cursor/rules/python.mdc` を参照してください
  - データベースに関する詳細な設定は `.cursor/rules/db.mdc` を参照してください
  - API仕様に関する詳細な設定は `.cursor/rules/api.mdc` を参照してください
  - フロントエンド開発に関する詳細な設定は `.cursor/rules/frontend.mdc` を参照してください

### Development Rules

- `.cursor/rules/`配下のすべてのルールファイルに従う
- コーディングガイドライン、API仕様、データベース設計はすべて`.cursor/rules/`で管理
- やり取りする上で明確になったルール、変更になったルールは都度`.cursor/rules/`に反映する

## Project Overview

SearchFace is a face recognition and similarity search application built with Python FastAPI backend and Next.js frontend. Users can upload images to find similar faces from a pre-built database using FAISS vector similarity search. The application uses Turso (SQLite-compatible cloud database) for data storage.

## Memories

- 作業完了後、ghコマンドを使ってPRを投げるところまで対応してください。説明には対応内容の詳細を記載してください。

[Rest of the file remains unchanged...]