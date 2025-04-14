import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime, timedelta

class LicenseManagementCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.license_file = os.path.join(self.base_path, "data", "licenses.json")
        self.vend_data_path = os.path.join(self.base_path, "data", "vend_data")
        self.admin_user_id = 1168991656834515109
        self.license_duration = 30
        self.license_price = 1500
        self.pending_licenses = {}  # ここに追加

    # 残りのメソッドは変更なし

    def load_licenses(self):
        if os.path.exists(self.license_file):
            with open(self.license_file, 'r') as f:
                return json.load(f)
        return {}

    def save_licenses(self, licenses):
        # ディレクトリが存在しない場合、作成する
        os.makedirs(os.path.dirname(self.license_file), exist_ok=True)
        
        with open(self.license_file, 'w') as f:
            json.dump(licenses, f)


    def check_license(self, user_id):
        licenses = self.load_licenses()
        if str(user_id) in licenses:
            expiry_date = datetime.fromisoformat(licenses[str(user_id)])
            if expiry_date > datetime.now():
                return True, expiry_date.strftime("%Y-%m-%d")
        return False, None
    @app_commands.command(name="ボット情報", description="ボットの使い方と機能の紹介")
    async def asinfo(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🤖 自販機ボットの使い方と機能紹介",
            description="このボットは、便利な自販機機能を提供します。以下の機能が利用可能です！",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="📋 主な機能",
            value=(
                "• `/自販機設置` - 自販機パネルを設置します\n"
                "• `/paypayログイン` - PayPayアカウントと連携します\n"
                "• `/ライセンス確認` - 自分のライセンス状態を確認します\n"
                "• `/ライセンス購入` - ライセンスの購入をリクエストします"
            ),
            inline=False
        )
        
        embed.add_field(
            name="💡 使い方のヒント",
            value=(
                "1. まずライセンスを購入してください（コマンドで購入可能）\n"
                "2. PayPayアカウントと連携します\n"
                "3. 自販機に詰めるものや価格などを設定\n"
                "4. 設定が完了後自販機を設置すれば自動で販売が行われます！"
            ),
            inline=False
        )
        
        
        embed.set_footer(text="自販機ボットをご利用いただきありがとうございます！")
        
        # ボットの招待ボタンを追加（オプション）
        view = discord.ui.View()
        invite_button = discord.ui.Button(
            style=discord.ButtonStyle.link,
            label="ボットを招待",
            url="https://discord.com/oauth2/authorize?client_id=1226918545468817490&permissions=8&integration_type=0&scope=bot"  # ここに実際のボット招待リンクを入れてください
        )
        view.add_item(invite_button)
        
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="ライセンス管理", description="ライセンスの追加・削除・確認を行います")
    @app_commands.default_permissions(administrator=True)
    async def manage_license(self, interaction: discord.Interaction, action: str, user: discord.User = None):
        if interaction.user.id != self.admin_user_id:
            await interaction.response.send_message("このコマンドは管理者のみ使用できます。", ephemeral=True)
            return

        await interaction.response.defer()

        licenses = self.load_licenses()
        
        embed = discord.Embed(title="ライセンス管理", color=discord.Color.blue())

        if action == "追加" and user:
            expiry_date = (datetime.now() + timedelta(days=self.license_duration)).isoformat()
            licenses[str(user.id)] = expiry_date
            self.save_licenses(licenses)
            embed.description = f"{user.mention} にライセンスを追加しました。"
            embed.add_field(name="有効期限", value=expiry_date, inline=False)
        elif action == "削除" and user:
            if str(user.id) in licenses:
                del licenses[str(user.id)]
                self.save_licenses(licenses)
                embed.description = f"{user.mention} のライセンスを削除しました。"
            else:
                embed.description = f"{user.mention} のライセンスは存在しません。"
                embed.color = discord.Color.red()
        elif action == "確認":
            if licenses:
                embed.description = "現在のライセンス情報:"
                for uid, date in licenses.items():
                    user = await self.bot.fetch_user(int(uid))
                    embed.add_field(name=f"{user.name}#{user.discriminator}", value=f"有効期限: {date}", inline=False)
            else:
                embed.description = "ライセンス情報はありません。"
        else:
            embed.description = "無効なアクションです。'追加'、'削除'、または '確認' を指定してください。"
            embed.color = discord.Color.red()

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="ライセンス確認", description="自分のライセンス状態を確認します")
    async def check_my_license(self, interaction: discord.Interaction):
        has_license, expiry_date = self.check_license(interaction.user.id)
        
        if has_license:
            embed = discord.Embed(title="ライセンス状態", description="有効なライセンスを持っています。", color=discord.Color.green())
            embed.add_field(name="有効期限", value=expiry_date, inline=False)
        else:
            embed = discord.Embed(title="ライセンス状態", description="有効なライセンスがありません。", color=discord.Color.red())
            embed.add_field(name="ライセンス料金", value=f"{self.license_price}円 / {self.license_duration}日", inline=False)
            embed.add_field(name="購入方法", value="管理者に連絡してください。", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="ライセンス直接購入", description="ライセンスを購入するためのリクエストを送信します")
    async def request_license(self, interaction: discord.Interaction):
        modal = LicensePurchaseModal()
        await interaction.response.send_modal(modal)

    @app_commands.command(name="ライセンス承認", description="ライセンス購入リクエストを承認します")
    @app_commands.default_permissions(administrator=True)
    async def approve_license(self, interaction: discord.Interaction, user_id: str):
        if interaction.user.id != self.admin_user_id:
            await interaction.response.send_message("このコマンドは管理者のみ使用できます。", ephemeral=True)
            return

        try:
            user_id_int = int(user_id)
        except ValueError:
            await interaction.response.send_message("無効なユーザーIDです。数字のみを入力してください。", ephemeral=True)
            return

        licenses = self.load_licenses()
        
        if str(user_id_int) not in self.pending_licenses:
            await interaction.response.send_message("このユーザーからのライセンス購入リクエストはありません。", ephemeral=True)
            return

        expiry_date = (datetime.now() + timedelta(days=self.license_duration)).isoformat()
        licenses[str(user_id_int)] = expiry_date
        self.save_licenses(licenses)

        del self.pending_licenses[str(user_id_int)]

        embed = discord.Embed(title="ライセンス承認", description=f"<@{user_id_int}> のライセンスを追加しました。", color=discord.Color.green())
        embed.add_field(name="有効期限", value=expiry_date, inline=False)
        await interaction.response.send_message(embed=embed)

        # ユーザーオブジェクトを取得してDMを送信
        try:
            user = await self.bot.fetch_user(user_id_int)
            await user.send("自販機のライセンスが追加されました。")
        except discord.errors.Forbidden:
            await interaction.followup.send(f"<@{user_id_int}> にDMを送信できませんでした。", ephemeral=True)
        except discord.errors.NotFound:
            await interaction.followup.send(f"ユーザーID: {user_id_int} が見つかりませんでした。", ephemeral=True)

class LicensePurchaseModal(discord.ui.Modal, title="ライセンス購入リクエスト"):
    def __init__(self):
        super().__init__()
        self.purchase_info = discord.ui.TextInput(
            label="1500円分のPayPayリンク",
            style=discord.TextStyle.paragraph,
            placeholder="開発者のDMに直接送られ使えるようになったらDMが来ます",
            min_length=41,
            max_length=41
        )
        self.add_item(self.purchase_info)

    async def on_submit(self, interaction: discord.Interaction):
        cog = interaction.client.get_cog("LicenseManagementCog")
        if cog:
            cog.pending_licenses[str(interaction.user.id)] = self.purchase_info.value
            admin = await interaction.client.fetch_user(cog.admin_user_id)
            try:
                await admin.send(f"ユーザー {interaction.user.mention} (ID: {interaction.user.id}) からライセンス購入リクエストがありました。\n"
                                 f"購入情報: {self.purchase_info.value}\n"
                                 f"承認するには `/ライセンス承認  を使用してください。")
                await interaction.response.send_message("ライセンス購入リクエストを送信しました。管理者の承認をお待ちください。", ephemeral=True)
                await admin.send(f"{interaction.user.id}")
            except discord.errors.Forbidden:
                await interaction.response.send_message("管理者にDMを送信できませんでした。管理者に直接連絡してください。", ephemeral=True)
        else:
            await interaction.response.send_message("エラーが発生しました。もう一度お試しください。", ephemeral=True)

async def setup(bot):
    await bot.add_cog(LicenseManagementCog(bot))