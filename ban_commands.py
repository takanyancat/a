import discord
from discord import app_commands
from discord.ui import View, Button
from discord.ext import commands


class BanView(View):
    """
    BANの確認と実行を行うUI型ビュー
    """

    def __init__(self, member: discord.Member, reason: str):
        super().__init__(timeout=60)  # タイムアウトを60秒に設定
        self.member = member
        self.reason = reason

    @discord.ui.button(label="BAN実行", style=discord.ButtonStyle.danger)
    async def execute_ban(self, interaction: discord.Interaction,
                          button: discord.ui.Button):
        """
        BANを実行するボタンの処理
        """
        guild = interaction.guild
        try:
            # メンバーをBANする
            await guild.ban(user=self.member, reason=self.reason)
            await interaction.response.send_message(
                f"🚫 **{self.member.name}** をBANしました。\n理由: {self.reason if self.reason else '理由はありません'}",
                ephemeral=False)
        except discord.Forbidden:
            await interaction.response.send_message("このメンバーをBANする権限がありません。",
                                                    ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(
                f"BAN実行中にエラーが発生しました: {str(e)}", ephemeral=True)

    @discord.ui.button(label="キャンセル", style=discord.ButtonStyle.secondary)
    async def cancel_ban(self, interaction: discord.Interaction,
                         button: discord.ui.Button):
        """
        BANをキャンセルするボタンの処理
        """
        await interaction.response.send_message("BANをキャンセルしました。",
                                                ephemeral=True)


class BanCommands(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ban", description="指定したメンバーを強制的にBANします。")
    @app_commands.describe(member="BANするメンバーを選択してください。",
                           reason="BANする理由を任意で記入してください。")
    @app_commands.checks.has_permissions(administrator=True)
    async def ban_member(self,
                         interaction: discord.Interaction,
                         member: discord.Member,
                         reason: str = None):
        """
        UI型BAN コマンドの処理
        """
        if not member:
            await interaction.response.send_message("BANするメンバーを指定してください。",
                                                    ephemeral=True)
            return

        if member == interaction.guild.owner:
            await interaction.response.send_message("サーバーオーナーをBANすることはできません。",
                                                    ephemeral=True)
            return

        # BANビューを表示
        embed = discord.Embed(
            title="BAN確認",
            description=
            f"以下のメンバーをBANしますか？\n\n**メンバー:** {member.mention}\n**理由:** {reason if reason else '理由はありません'}",
            color=discord.Color.red())
        view = BanView(member, reason)
        await interaction.response.send_message(embed=embed,
                                                view=view,
                                                ephemeral=True)


async def setup_ban_commands(bot: commands.Bot):
    """
    BAN コマンドを Bot に登録します。
    """
    await bot.add_cog(BanCommands(bot))
