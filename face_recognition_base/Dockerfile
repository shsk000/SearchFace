FROM python:3.10.17

# 作業ディレクトリを設定
WORKDIR /app

# dlib / face_recognition / OpenCV に必要なシステム依存パッケージをすべてインストール
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    libboost-all-dev \
    libsqlite3-dev \
    libglib2.0-0 \
    libpython3-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip setuptools wheel

RUN pip install --use-pep517 dlib==19.24.8

RUN pip install --use-pep517 face_recognition==1.3.0 opencv-python numpy pillow

ENV PYTHONPATH=/app