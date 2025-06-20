from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import search, ranking
from src.api.routes.persons import router as persons_router
from src.core.middleware import error_handler_middleware
import uvicorn
from contextlib import asynccontextmanager
import asyncio
from src.database import db_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクルイベント"""
    # 起動時: DB接続をバックグラウンドで実行
    loop = asyncio.get_running_loop()
    loop.create_task(asyncio.to_thread(db_manager.connect_to_databases))

    yield

    # 終了時
    db_manager.close_database_connections()

# アプリケーションの作成
app = FastAPI(
    title="SearchFace API",
    description="顔画像の類似検索API",
    version="1.0.0",
    lifespan=lifespan
)

# CORSミドルウェア設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切に制限する
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# エラーハンドリングミドルウェアの追加
app.middleware("http")(error_handler_middleware)

# ルートエンドポイント
@app.get("/")
async def root():
    """ヘルスチェック用のルートエンドポイント"""
    return {"status": "ok", "message": "SearchFace API is running"}

# ルーティングの登録
app.include_router(search.router, prefix="/api")
app.include_router(ranking.router, prefix="/api")
app.include_router(persons_router, prefix="/api")

# 起動用関数
def start(host="0.0.0.0", port=10000):
    """アプリケーションを起動する

    Args:
        host (str): ホストアドレス
        port (int): ポート番号
    """
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    start()
