# Alcheck (アルチェック) - Discord Bot

Discordで飲んだアルコールを記録し、ウィドマーク式で血中アルコール濃度（BAC）を計算・酔いの程度を判定するボット。

## 機能

- 🍺 **アルコール摂取記録**: 飲んだお酒の種類と量を記録
- 🧠 **BAC計算**: ウィドマーク式による血中アルコール濃度の推定
- 🎭 **酔い度判定**: BACに基づいて現在の酔いの段階を表示
- ⏰ **24時間追跡**: 過去24時間の累計アルコール摂取量を管理
- 👤 **User Install対応**: サーバーとユーザー両方でインストール可能

## 使い方

### 1. プロフィール設定

最初に性別と体重を設定します（一度設定すれば保存されます）：

```
/alcheck-set 性別:(男性|女性) 体重:(kg)
```

**例**: `/alcheck-set 性別:男性 体重:70`

### 2. アルコール記録

飲んだお酒を記録します：

```
/alcheck 酒:(種類) グラス:(サイズ)
```

**例**: 
- `/alcheck 酒:ビール グラス:缶`
- `/alcheck 酒:日本酒 グラス:徳利`
- `/alcheck 酒:12 グラス:250` （カスタム度数12%、250mL）

### プリセット一覧

#### お酒の種類
- **ビール** (5%): 缶、ロング缶、グラス、ジョッキ、大ジョッキ
- **ハイボール** (7%): グラス、大グラス、ロンググラス
- **日本酒** (15%): 徳利、もっきり、お猪口
- **ワイン** (12%): グラス（小）、グラス、グラス（大）
- **焼酎** (20%): ロック、ソーダ割、お猪口
- **ウイスキー** (40%): シングル、ダブル、ロック

> **カスタム入力**: 数値を直接入力して度数(%)や容量(mL)を指定できます

### 酔いの段階

| BAC (%) | 段階 | 状態 |
|---------|------|------|
| 0.00～0.02 | 通常 | 酔いなし |
| 0.02～0.04 | 爽快期 | 気分が良くなる |
| 0.05～0.10 | ほろ酔い期 | 顔が赤くなる、陽気になる |
| 0.11～0.15 | 酩酊初期 | バランス感覚が悪くなる |
| 0.16～0.30 | 酩酊極期 | 思考・判断が低下 |
| 0.31～0.40 | 泥酔期 | 動けない状態 |
| 0.41～ | 昏睡期 | ⚠️ 危険：医療対応が必要 |

## セットアップ

### 必要なもの

- Docker & Docker Compose
- Discord Bot Token & Application ID

### インストール手順

1. **リポジトリをクローン**

```bash
git clone https://github.com/yourusername/alcheck-discordbot.git
cd alcheck-discordbot
```

2. **環境変数の設定**

`.env.example` をコピーして `.env` を作成し、Discord のトークンを設定：

```bash
cp .env.example .env
```

`.env` を編集：

```env
DISCORD_TOKEN=your_discord_bot_token_here
APPLICATION_ID=your_application_id_here
```

3. **Dockerで起動**

```bash
docker-compose up -d
```

4. **ログ確認**

```bash
docker-compose logs -f
```

### Discord Bot の作成

1. [Discord Developer Portal](https://discord.com/developers/applications) にアクセス
2. 「New Application」をクリックして新しいアプリケーションを作成
3. 「Bot」セクションでボットを作成し、トークンをコピー
4. 「General Information」でApplication IDをコピー
5. 「Installation」セクションで：
   - **Guild Install**: `applications.commands` スコープを追加
   - **User Install**: `applications.commands` スコープを追加
6. 「Bot」セクションで以下の権限を有効化：
   - Message Content Intent（オプション）

## カスタマイズ

### お酒とグラスのプリセットを編集

[config.json](config.json) を編集することで、お酒の種類やグラスサイズを追加・変更できます：

```json
{
  "drinks": {
    "your_drink": {
      "name": "表示名",
      "percentage": 度数(%),
      "glasses": {
        "glass_type": {
          "name": "グラス名",
          "ml": 容量(mL)
        }
      }
    }
  }
}
```

変更後、Dockerコンテナを再起動：

```bash
docker-compose restart
```

## 技術スタック

- **言語**: Python 3.11
- **ライブラリ**: discord.py 2.4.0
- **データ保存**: JSON
- **実行環境**: Docker

## 注意事項

⚠️ このボットは**あくまで推定値**を提供するものであり、医療的な診断ツールではありません。

- 実際の血中アルコール濃度は個人差や多くの要因により異なります
- 飲酒運転は絶対にしないでください
- 体調が悪い場合は医療機関に相談してください

## ライセンス

MIT License - 詳細は [LICENSE](LICENSE) を参照してください。
