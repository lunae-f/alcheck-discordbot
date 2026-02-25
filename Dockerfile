# Python 3.11 ベースイメージ
FROM python:3.11-slim

# 作業ディレクトリの設定
WORKDIR /app

# 依存関係ファイルをコピー
COPY requirements.txt .

# 依存関係のインストール
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションファイルをコピー
COPY . .

# データディレクトリの作成
RUN mkdir -p /app/data

# ボリュームの設定（データ永続化用）
VOLUME ["/app/data"]

# Botの実行
CMD ["python", "bot.py"]
