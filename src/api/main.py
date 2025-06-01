from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# アプリケーションの作成
app = FastAPI(
    title="SearchFace API",
    description="顔画像の類似検索API",
    version="1.0.0"
)

# CORSミドルウェア設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切に制限する
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルートエンドポイント
@app.get("/")
async def root():
    """ヘルスチェック用のルートエンドポイント"""
    return {"status": "ok", "message": "SearchFace API is running"}

# ルーティングのインポート
from api.routes import search

# ルーティングの登録
app.include_router(search.router)

# 起動用関数
def start(host="0.0.0.0", port=8000):
    """アプリケーションを起動する
    
    Args:
        host (str): ホストアドレス
        port (int): ポート番号
    """
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    start()
