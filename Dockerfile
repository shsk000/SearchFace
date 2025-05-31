# Python 3.11.12をベースイメージとして使用
FROM python:3.11.12-slim

# 必要なシステムパッケージをインストール
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリを設定
WORKDIR /app

# 必要なファイルをコピー
COPY requirements.txt .
COPY src/ ./src/
COPY data/face_database.db ./data/
COPY data/face.index ./data/

# Pythonパッケージをインストール
RUN pip install --no-cache-dir -r requirements.txt

# 環境変数を設定
ENV PYTHONPATH=/app

# ポートを公開
EXPOSE 8000

# アプリケーションを起動
CMD ["python", "src/api/main.py"] 