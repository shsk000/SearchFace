# 開発環境用
FROM node:22-alpine

WORKDIR /app

# 依存関係のインストール
COPY package*.json ./
RUN npm install

# ソースコードのコピー
COPY . .

# 環境変数の設定
ENV NODE_ENV=development
ENV PORT=3000

# ポートの公開
EXPOSE 3000

# アプリケーションの起動（docker-composeで上書き）
CMD ["npm", "run", "dev"] 