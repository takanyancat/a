import discord
from discord import app_commands
from discord.ext import commands


class MessageBackup:
    """
    チャンネルのプロパティやメッセージ履歴をバックアップするためのクラス。
    """

    def __init__(self):
        self.messages = []
        self.channel_properties = {}

    def clear(self):
        """
        バックアップをクリアします。
        """
        self.messages = []
        self.channel_properties = {}


# グローバルなバックアップインスタンス
message_backup = MessageBackup()


class Nuke(commands.Cog):
    """
    チャンネルを削除してバックアップ、または復元するためのコマンドクラス。
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="nuke", description="指定したチャンネルを削除して自動的に復元します。")
    @app_commands.describe(channel="削除してバックアップを作成するチャンネルを指定してください。")
    @app_commands.default_permissions(manage_channels=True)
    async def nuke(self, interaction: discord.Interaction,
                   channel: discord.TextChannel):
        """
        チャンネルを削除し、自動的に復元します。
        """
        try:
            # 即座にインタラクション応答
            await interaction.response.send_message(
                f"チャンネル `{channel.name}` の削除と復元を開始します...", ephemeral=True)

            # 既存バックアップをクリア
            message_backup.clear()

            # チャンネルプロパティをバックアップ
            message_backup.channel_properties = {
                "name": channel.name,
                "category_id":
                channel.category.id if channel.category else None,
                "topic": channel.topic,
                "slowmode_delay": channel.slowmode_delay,
                "nsfw": channel.is_nsfw(),
                "overwrites": channel.overwrites,
                "position": channel.position,
            }

            # メッセージ履歴をバックアップ
            async for message in channel.history(limit=None,
                                                 oldest_first=True):
                message_backup.messages.append({
                    "content":
                    message.content,
                    "author_name":
                    message.author.display_name,
                    "author_avatar":
                    message.author.avatar.url
                    if message.author.avatar else None,
                })

            # チャンネルを削除
            await channel.delete()

            # チャンネルを自動復元
            category = discord.utils.get(
                interaction.guild.categories,
                id=message_backup.channel_properties.get("category_id"))

            restored_channel = await interaction.guild.create_text_channel(
                name=message_backup.channel_properties["name"],
                category=category,
                topic=message_backup.channel_properties.get("topic", ""),
                slowmode_delay=message_backup.channel_properties.get(
                    "slowmode_delay", 0),
                nsfw=message_backup.channel_properties.get("nsfw", False),
                overwrites=message_backup.channel_properties.get(
                    "overwrites", {}),
            )

            # 元の位置に配置
            await restored_channel.edit(
                position=message_backup.channel_properties["position"])
            await interaction.followup.send(
                f"チャンネル `{restored_channel.name}` が自動復元されました。", ephemeral=True)

        except discord.Forbidden:
            await interaction.followup.send("Botに必要な権限が不足しています。",
                                            ephemeral=True)
        except discord.HTTPException as e:
            await interaction.followup.send(f"HTTPエラーが発生しました: {e}",
                                            ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"予期しないエラーが発生しました: {e}",
                                            ephemeral=True)

    @app_commands.command(name="unnuke", description="チャンネル内で話されたメッセージを復元します。")
    @app_commands.default_permissions(manage_channels=True)
    async def unke(self, interaction: discord.Interaction):
        """
        チャンネル内で話されたメッセージを復元します。
        """
        if not message_backup.channel_properties:
            await interaction.response.send_message(
                "バックアップされたチャンネル情報が見つかりません。", ephemeral=True)
            return

        try:
            # 現在のチャンネルにメッセージ履歴を復元
            for msg in message_backup.messages:
                if msg["content"]:
                    embed = discord.Embed(description=msg['content'],
                                          color=discord.Color.blue())
                    embed.set_author(name=msg['author_name'],
                                     icon_url=msg["author_avatar"]
                                     if msg["author_avatar"] else None)
                    await interaction.channel.send(embed=embed)

            await interaction.response.send_message("メッセージ履歴を復元しました。",
                                                    ephemeral=True)

        except discord.Forbidden:
            await interaction.response.send_message("Botに必要な権限が不足しています。",
                                                    ephemeral=True)
        except discord.HTTPException as e:
            await interaction.response.send_message(f"HTTPエラーが発生しました: {e}",
                                                    ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"予期しないエラーが発生しました: {e}",
                                                    ephemeral=True)


async def setup(bot: commands.Bot):
    """
    Nuke CogをBotに登録します。
    """
    await bot.add_cog(Nuke(bot))
