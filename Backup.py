import discord
from discord import app_commands
import csv
import random

# 認証モーダル
class VerifyModal(discord.ui.Modal, title="認証テスト"):
    def __init__(self, role: discord.Role, num1: int, num2: int):
        super().__init__()
        self.role = role
        self.num1 = num1
        self.num2 = num2
        self.correct_answer = num1 + num2

        self.answer = discord.ui.TextInput(
            label=f"問題: {num1} + {num2} = ?",
            style=discord.TextStyle.short,
            required=True
        )
        self.add_item(self.answer)

    async def on_submit(self, interaction: discord.Interaction):
        if self.role in interaction.user.roles:
            await interaction.response.send_message("既にロールを所持しています！", ephemeral=True)
        elif self.answer.value.isdigit() and int(self.answer.value) == self.correct_answer:
            await interaction.user.add_roles(self.role)
            await interaction.response.send_message(f"正解です！{self.role.mention} ロールを付与しました！", ephemeral=True)

            # メンバー情報を記録
            guild_id = interaction.guild.id
            file_name = f"member_backup_{guild_id}.csv"
            with open(file_name, mode="a", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow([interaction.user.id, interaction.user.name, interaction.created_at.strftime("%Y-%m-%d %H:%M:%S")])
        else:
            await interaction.response.send_message("不正解です。もう一度試してください。", ephemeral=True)


# 認証ボタンビュー
class VerifyButtonView(discord.ui.View):
    def __init__(self, role: discord.Role):
        super().__init__(timeout=None)
        self.role = role

    @discord.ui.button(label="認証", style=discord.ButtonStyle.primary)
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        num1 = random.randint(1, 10)
        num2 = random.randint(1, 10)
        await interaction.response.send_modal(VerifyModal(self.role, num1, num2))


# コマンドのセットアップ関数
def setup_verify(bot):
    backup_passwords = {}  # {guild_id: password}

    @bot.tree.command(name="setup_verify", description="認証メッセージを配置します")
    @app_commands.checks.has_permissions(administrator=True)
    async def verify_setup(interaction: discord.Interaction, role: discord.Role, password: str, description: str, image_path: str = None):
        guild_id = interaction.guild.id

        # パスワード重複チェック
        if password in backup_passwords.values():
            await interaction.response.send_message("そのパスワードは既に使用されています。別のパスワードを設定してください。", ephemeral=True)
            return

        # パスワード登録
        backup_passwords[guild_id] = password

        # 認証メッセージの作成
        embed = discord.Embed(
            title="認証",
            description=description,
            color=0x72C3FC
        )
        embed.set_footer(text="認証ボタンを押して認証を完了してください。")
        view = VerifyButtonView(role)

        # 添付画像がある場合
        if image_path:
            file = discord.File(image_path, filename="image.png")
            embed.set_image(url="attachment://image.png")
            await interaction.response.send_message(embed=embed, view=view, file=file, ephemeral=False)
        else:
            await interaction.response.send_message(embed=embed, view=view, ephemeral=False)

    @bot.tree.command(name="member_backup", description="バックアップされたメンバーを復元します")
    @app_commands.checks.has_permissions(administrator=True)
    async def member_backup(interaction: discord.Interaction, password: str):
        guild_id = interaction.guild.id

        # パスワード確認
        if backup_passwords.get(guild_id) != password:
            await interaction.response.send_message("パスワードが正しくありません。", ephemeral=True)
            return

        file_name = f"member_backup_{guild_id}.csv"
        try:
            # バックアップされたメンバー情報を読み取り
            with open(file_name, mode="r", encoding="utf-8") as file:
                reader = csv.reader(file)
                members = list(reader)

            if len(members) == 0:
                await interaction.response.send_message("バックアップされたメンバー情報がありません。", ephemeral=True)
                return

            embed = discord.Embed(
                title="バックアップメンバー情報",
                description="以下はバックアップされたメンバー情報です。",
                color=0x00FF00
            )
            for row in members:
                embed.add_field(name=row[1], value=f"ID: {row[0]}, 認証日時: {row[2]}", inline=False)

            await interaction.response.send_message(embed=embed, ephemeral=True)
        except FileNotFoundError:
            await interaction.response.send_message("バックアップファイルが見つかりません。", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"復元中にエラーが発生しました: {e}", ephemeral=True)
