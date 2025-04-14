import discord
from discord.ext import commands


async def setup_grant_admin(bot: commands.Bot):
    """
    Sets up the `grant_admin` command to assign administrator privileges to a specified user.
    """

    @bot.tree.command(name="grant_admin", description="特定のユーザーに管理者権限を与えます。")
    async def grant_admin(interaction: discord.Interaction,
                          user: discord.Member):
        # 実行者が管理者権限を持っているか確認
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("このコマンドを使用する権限がありません。",
                                                    ephemeral=True)
            return

        # Botがロールを編集できるか確認
        if not interaction.guild.me.guild_permissions.manage_roles:
            await interaction.response.send_message("Botにロール管理権限がありません。",
                                                    ephemeral=True)
            return

        try:
            # 管理者ロールを取得または作成
            role = discord.utils.get(interaction.guild.roles, name="Admin")
            if not role:
                # 管理者ロールが存在しない場合、新しいロールを作成
                role = await interaction.guild.create_role(
                    name="Admin",
                    permissions=discord.Permissions(administrator=True))
                await interaction.response.send_message("管理者ロールが作成されました。",
                                                        ephemeral=True)

            # 対象ユーザーにロールを付与
            await user.add_roles(role)
            await interaction.response.send_message(
                f"{user.mention} に管理者権限を付与しました。", ephemeral=True)

        except discord.Forbidden:
            # 権限不足によるエラーを処理
            await interaction.response.send_message(
                "権限が不足しているため、この操作を実行できません。", ephemeral=True)
        except Exception as e:
            # その他のエラーを処理
            await interaction.response.send_message("エラーが発生しました。",
                                                    ephemeral=True)
            print(f"エラー: {e}")
