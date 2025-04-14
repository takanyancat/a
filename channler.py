    import discord
    from discord import app_commands
    from discord.ext import commands

    class Channeler(commands.Cog):
        def __init__(self, bot):
            self.bot = bot

        @app_commands.command(name="create_channel", description="新しいチャンネルを作成します")
        @app_commands.describe(
            is_private="プライベートチャンネルにする場合はTrue",
            channel_name="新しいチャンネルの名前"
        )
        async def create_channel(self, interaction: discord.Interaction, channel_name: str, is_private: bool = False):
            """
            新しいチャンネルを作成するコマンド。
            """
            # 権限チェック
            if not interaction.user.guild_permissions.manage_channels:
                await interaction.response.send_message("あなたにはチャンネルを管理する権限がありません。", ephemeral=True)
                return

            try:
                # プライベートチャンネル用の権限設定
                overwrites = None
                if is_private:
                    overwrites = {
                        interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                        interaction.user: discord.PermissionOverwrite(read_messages=True)
                    }

                # テキストチャンネルを作成
                new_channel = await interaction.guild.create_text_channel(
                    name=channel_name,
                    overwrites=overwrites
                )
                await interaction.response.send_message(f"チャンネル `{new_channel.name}` が作成されました。")
            except discord.Forbidden:
                await interaction.response.send_message("Botに必要な権限が不足しています。", ephemeral=True)
            except discord.HTTPException as e:
                await interaction.response.send_message(f"HTTPエラーが発生しました: {e}", ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(f"予期しないエラーが発生しました: {e}", ephemeral=True)

    async def setup(bot):
        await bot.add_cog(Channeler(bot))