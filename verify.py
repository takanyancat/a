import discord
from discord import app_commands
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
        member = interaction.guild.get_member(interaction.user.id)
        if not member:
            await interaction.response.send_message("メンバー情報が見つかりません。", ephemeral=True)
            return

        if self.role in member.roles:
            await interaction.response.send_message("既にロールを所持しています！", ephemeral=True)
            return

        if self.answer.value.isdigit() and int(self.answer.value) == self.correct_answer:
            await member.add_roles(self.role)
            await interaction.response.send_message(
                f"正解です！{self.role.mention} ロールを付与しました！", ephemeral=True
            )
        else:
            await interaction.response.send_message("不正解です。もう一度試してください。", ephemeral=True)

async def setup_verify(bot: discord.Client):
    @bot.tree.command(name="verify_setup", description="認証メッセージを配置します")
    @app_commands.checks.has_permissions(administrator=True)
    async def verify_setup(
        interaction: discord.Interaction, role: discord.Role, description: str
    ):
        if role.is_default():
            await interaction.response.send_message("デフォルトロールは使用できません。", ephemeral=True)
            return

        num1 = random.randint(1, 10)
        num2 = random.randint(1, 10)

        # Create and display the VerifyModal
        await interaction.response.send_modal(VerifyModal(role, num1, num2))