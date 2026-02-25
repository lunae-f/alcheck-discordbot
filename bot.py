import discord
from discord.ext import commands
import os
import json
import logging
from dotenv import load_dotenv
from pathlib import Path

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# .env ファイルを読み込む
load_dotenv()

# 環境変数の取得
TOKEN = os.getenv('DISCORD_TOKEN')
APPLICATION_ID = os.getenv('APPLICATION_ID')

if not TOKEN:
    logger.error("DISCORD_TOKEN が .env ファイルに設定されていません")
    exit(1)

if not APPLICATION_ID:
    logger.error("APPLICATION_ID が .env ファイルに設定されていません")
    exit(1)

# config.json の読み込み
CONFIG_PATH = Path(__file__).parent / 'config.json'
try:
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = json.load(f)
    logger.info("config.json を読み込みました")
except FileNotFoundError:
    logger.error("config.json が見つかりません")
    exit(1)
except json.JSONDecodeError as e:
    logger.error(f"config.json の形式が正しくありません: {e}")
    exit(1)

# データディレクトリの作成
DATA_DIR = Path(__file__).parent / 'data'
DATA_DIR.mkdir(exist_ok=True)

# Bot の初期化
class AlcheckBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        
        super().__init__(
            command_prefix='!',  # スラッシュコマンドを使うので実質未使用
            intents=intents,
            application_id=int(APPLICATION_ID)
        )
        
        self.config = config
        self.data_dir = DATA_DIR
        
    async def setup_hook(self):
        """Bot起動時の初期化処理"""
        # Cogsの読み込み
        await self.load_extension('cogs.alcheck')
        logger.info("Cogs を読み込みました")
        
        # コマンドの同期
        await self.tree.sync()
        logger.info("コマンドを同期しました")
        
    async def on_ready(self):
        """Bot準備完了時の処理"""
        logger.info(f'ログインしました: {self.user.name} (ID: {self.user.id})')
        logger.info(f'discord.py バージョン: {discord.__version__}')
        logger.info('Alcheck Bot が起動しました')

def main():
    """メイン関数"""
    bot = AlcheckBot()
    
    try:
        bot.run(TOKEN)
    except discord.LoginFailure as e:
        logger.error(f"Discord へのログインに失敗しました: {e}")
        logger.error(f"トークンの長さ: {len(TOKEN) if TOKEN else 0}")
        logger.error("Discord Developer Portal でトークンを再生成してください")
    except Exception as e:
        logger.error(f"予期しないエラーが発生しました: {e}", exc_info=True)

if __name__ == '__main__':
    main()
