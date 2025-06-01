# すでにface_recognition等を含むカスタムイメージをベースに使用
FROM shsk959/face_recognition_base:latest

# 作業ディレクトリを設定
WORKDIR /app

# アプリのコードと依存ファイルをコピー
COPY requirements.txt ./
COPY src/ ./src/

# face_recognition系は除外した requirements.txt を使ってpip install
# face_recognition==1.3.0	
# dlib==19.24.0 〜 19.24.8
# opencv-python
# numpy, pillow
# face_recognition_models==0.3.0
RUN pip install --no-cache-dir -r requirements.txt

RUN echo "R2_BUCKET_NAME: ${R2_BUCKET_NAME}"

# データの事前ダウンロード
RUN python src/utils/r2_uploader.py --action download

# 環境変数の設定（任意）
ENV PYTHONPATH=/app

# ポートを公開（FastAPIやUvicorn用）
EXPOSE 8000

# アプリケーション起動
CMD ["python", "src/run_api.py"]
