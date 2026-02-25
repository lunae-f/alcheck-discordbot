import discord
from discord import app_commands
from discord.ext import commands
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List
import pytz

logger = logging.getLogger(__name__)

# 日本のタイムゾーン
JST = pytz.timezone('Asia/Tokyo')

class AlcheckCog(commands.Cog):
    """アルコール記録・血中アルコール濃度計算コマンド"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = bot.config
        self.data_file = bot.data_dir / 'users.json'
        self.users_data = self._load_users_data()
        
    def _load_users_data(self) -> dict:
        """ユーザーデータの読み込み"""
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.error("users.json の形式が正しくありません")
                return {}
        return {}
    
    def _save_users_data(self):
        """ユーザーデータの保存"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.users_data, f, ensure_ascii=False, indent=2)
    
    def _get_user_data(self, user_id: str) -> Optional[dict]:
        """指定ユーザーのデータを取得"""
        return self.users_data.get(user_id)
    
    def _set_user_profile(self, user_id: str, gender: str, weight: float):
        """ユーザープロフィールを設定"""
        if user_id not in self.users_data:
            self.users_data[user_id] = {
                "gender": gender,
                "weight_kg": weight,
                "records": []
            }
        else:
            self.users_data[user_id]["gender"] = gender
            self.users_data[user_id]["weight_kg"] = weight
        self._save_users_data()
    
    def _add_record(self, user_id: str, alcohol_grams: float):
        """飲酒記録を追加"""
        now = datetime.now(JST).isoformat()
        self.users_data[user_id]["records"].append({
            "timestamp": now,
            "alcohol_grams": alcohol_grams
        })
        self._save_users_data()
    
    def _clean_old_records(self, user_id: str):
        """24時間以前の記録を削除"""
        user_data = self.users_data.get(user_id)
        if not user_data:
            return
        
        cutoff_time = datetime.now(JST) - timedelta(hours=24)
        user_data["records"] = [
            record for record in user_data["records"]
            if datetime.fromisoformat(record["timestamp"]) > cutoff_time
        ]
        self._save_users_data()
    
    def _calculate_bac(self, user_id: str) -> tuple[float, float]:
        """
        血中アルコール濃度を計算
        Returns: (BAC, total_alcohol_grams)
        """
        user_data = self._get_user_data(user_id)
        if not user_data or not user_data.get("records"):
            return 0.0, 0.0
        
        weight = user_data["weight_kg"]
        gender = user_data["gender"]
        coefficient = self.config["gender_coefficient"][gender]
        elimination_rate = self.config["elimination_rate_per_hour"]
        
        now = datetime.now(JST)
        total_bac = 0.0
        total_alcohol = 0.0
        
        for record in user_data["records"]:
            timestamp = datetime.fromisoformat(record["timestamp"])
            alcohol_grams = record["alcohol_grams"]
            
            # 経過時間（時間単位）
            hours_passed = (now - timestamp).total_seconds() / 3600
            
            # この記録による初期BAC
            initial_bac = alcohol_grams / (weight * coefficient) / 10  # %に変換
            
            # 排出分を差し引く
            eliminated_bac = elimination_rate * hours_passed
            current_bac = max(0, initial_bac - eliminated_bac)
            
            total_bac += current_bac
            total_alcohol += alcohol_grams
        
        return total_bac, total_alcohol
    
    def _get_bac_stage(self, bac: float) -> tuple[str, str]:
        """
        BAC値から酔いの段階を取得
        Returns: (stage_name, description)
        """
        stages = self.config["bac_stages"]
        stage_thresholds = sorted([float(k) for k in stages.keys()], reverse=True)
        
        for threshold in stage_thresholds:
            if bac >= threshold:
                stage_data = stages[str(threshold)]
                return stage_data["name"], stage_data["description"]
        
        # デフォルト
        return "通常", "酔いなし"
    
    @app_commands.command(name="alcheck-set", description="体重と性別を設定します")
    @app_commands.describe(
        gender="性別を選択してください",
        weight="体重を入力してください（kg）"
    )
    @app_commands.choices(gender=[
        app_commands.Choice(name="男性", value="male"),
        app_commands.Choice(name="女性", value="female")
    ])
    async def alcheck_set(
        self,
        interaction: discord.Interaction,
        gender: app_commands.Choice[str],
        weight: float
    ):
        """プロフィール設定コマンド"""
        user_id = str(interaction.user.id)
        
        if weight <= 0:
            await interaction.response.send_message(
                "❌ 体重は正の数値を入力してください",
                ephemeral=True
            )
            return
        
        self._set_user_profile(user_id, gender.value, weight)
        
        gender_display = "男性" if gender.value == "male" else "女性"
        embed = discord.Embed(
            title="✅ プロフィールを設定しました",
            color=discord.Color.green()
        )
        embed.add_field(name="性別", value=gender_display, inline=True)
        embed.add_field(name="体重", value=f"{weight} kg", inline=True)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="alcheck", description="飲んだアルコールを記録します")
    @app_commands.describe(
        drink="お酒の種類を選択してください",
        glass="飲んだ量を選択してください"
    )
    async def alcheck(
        self,
        interaction: discord.Interaction,
        drink: str,
        glass: str
    ):
        """アルコール記録コマンド"""
        user_id = str(interaction.user.id)
        
        # プロフィール確認
        user_data = self._get_user_data(user_id)
        if not user_data:
            await interaction.response.send_message(
                "❌ 先に `/alcheck-set` でプロフィールを設定してください",
                ephemeral=True
            )
            return
        
        # 古い記録を削除
        self._clean_old_records(user_id)
        
        # お酒の情報を取得
        drink_info = None
        drink_name = None
        percentage = None
        
        # プリセットから検索
        if drink in self.config["drinks"]:
            drink_info = self.config["drinks"][drink]
            drink_name = drink_info["name"]
            percentage = drink_info["percentage"]
        else:
            # 数値（度数）として解析を試みる
            try:
                percentage = float(drink)
                drink_name = f"{percentage}%"
            except ValueError:
                await interaction.response.send_message(
                    f"❌ お酒の種類 `{drink}` が見つかりません",
                    ephemeral=True
                )
                return
        
        # グラスの情報を取得
        ml = None
        glass_name = None
        
        if drink_info and glass in drink_info["glasses"]:
            glass_info = drink_info["glasses"][glass]
            glass_name = glass_info["name"]
            ml = glass_info["ml"]
        else:
            # 数値（mL）として解析を試みる
            try:
                ml = float(glass)
                glass_name = f"{ml} mL"
            except ValueError:
                await interaction.response.send_message(
                    f"❌ グラスサイズ `{glass}` が見つかりません",
                    ephemeral=True
                )
                return
        
        # アルコール量を計算
        alcohol_density = self.config["alcohol_density"]
        alcohol_grams = ml * (percentage / 100) * alcohol_density
        
        # 記録を追加
        self._add_record(user_id, alcohol_grams)
        
        # 現在のBACを計算
        bac, total_alcohol = self._calculate_bac(user_id)
        stage_name, stage_desc = self._get_bac_stage(bac)
        
        # 結果を表示
        embed = discord.Embed(
            title="✅ 記録しました",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="🍺 摂取内容",
            value=f"{drink_name} × {glass_name}",
            inline=False
        )
        embed.add_field(
            name="📊 摂取アルコール量",
            value=f"{alcohol_grams:.1f} g",
            inline=False
        )
        embed.add_field(
            name="🧠 血中アルコール濃度",
            value=f"**{bac:.3f}%**",
            inline=True
        )
        embed.add_field(
            name="🎭 判定",
            value=f"**{stage_name}**\n{stage_desc}",
            inline=True
        )
        embed.add_field(
            name="⏰ 過去24時間の累計",
            value=f"{total_alcohol:.1f} g",
            inline=False
        )
        
        # 警告表示
        if bac >= 0.31:
            embed.set_footer(text="⚠️ 危険な状態です。飲酒を控え、必要に応じて医療機関に相談してください。")
        elif bac >= 0.16:
            embed.set_footer(text="⚠️ かなり酔っています。これ以上の飲酒は控えましょう。")
        
        await interaction.response.send_message(embed=embed)
    
    @alcheck.autocomplete('drink')
    async def drink_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str
    ) -> List[app_commands.Choice[str]]:
        """お酒の種類のオートコンプリート"""
        drinks = self.config["drinks"]
        choices = []
        
        for key, value in drinks.items():
            if current.lower() in key.lower() or current in value["name"]:
                choices.append(app_commands.Choice(
                    name=f"{value['name']} ({value['percentage']}%)",
                    value=key
                ))
        
        # 数値入力のヒント
        if current.replace('.', '').isdigit():
            choices.insert(0, app_commands.Choice(
                name=f"カスタム度数: {current}%",
                value=current
            ))
        
        return choices[:25]  # Discord の上限
    
    @alcheck.autocomplete('glass')
    async def glass_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str
    ) -> List[app_commands.Choice[str]]:
        """グラスサイズのオートコンプリート"""
        # 現在選択されているお酒の種類を取得
        # Note: interaction.namespace を使って現在の入力値にアクセス
        try:
            drink = interaction.namespace.drink
        except:
            drink = None
        
        choices = []
        
        # お酒が選択されている場合、そのグラスオプションを表示
        if drink and drink in self.config["drinks"]:
            drink_info = self.config["drinks"][drink]
            for key, value in drink_info["glasses"].items():
                if current.lower() in key.lower() or current in value["name"]:
                    choices.append(app_commands.Choice(
                        name=f"{value['name']} ({value['ml']} mL)",
                        value=key
                    ))
        
        # 数値入力のヒント
        if current.replace('.', '').isdigit():
            choices.insert(0, app_commands.Choice(
                name=f"カスタム容量: {current} mL",
                value=current
            ))
        
        return choices[:25]  # Discord の上限

async def setup(bot: commands.Bot):
    """Cogのセットアップ"""
    await bot.add_cog(AlcheckCog(bot))
    logger.info("AlcheckCog をロードしました")
