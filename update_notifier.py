import discord
from discord.ext import commands

# ハードコードされたパスワード（管理者のみが知っている）
ADMIN_PASSWORD = "taka1127aki"

async def notify_update(bot: commands.Bot):
    """Botの更新通知を導入しているすべてのサーバーに送信します。"""
    update_message = (
        "⚠️ **更新が必要です！**\n"
        "管理者は[こちら](https://discord.com/oauth2/authorize?client_id=1357247548472954881)から更新をお願いします。@everyone"
    )
    for guild in bot.guilds:
        try:
            # 優先度: システムチャンネル -> 送信権限のある最初のテキストチャンネル
            target_channel = guild.system_channel or next(
                (channel for channel in guild.text_channels if channel.permissions_for(guild.me).send_messages), None
            )

            if target_channel:
                # 既存の通知メッセージを削除
                async for message in target_channel.history(limit=50):
                    if update_message in message.content:
                        await message.delete()

                # 通知を送信してピン留め
                sent_message = await target_channel.send(update_message)
                await sent_message.pin()
                print(f"更新通知を送信しました: {guild.name} ({guild.id})")
            else:
                print(f"通知を送信するチャンネルが見つかりませんでした: {guild.name} ({guild.id})")

        except discord.Forbidden:
            print(f"権限不足のため通知を送信できませんでした: {guild.name} ({guild.id})")
        except Exception as e:
            print(f"サーバー {guild.name} ({guild.id}) への通知に失敗しました: {e}")


async def setup_update_notifier(bot: commands.Bot):
    """コマンドとして更新通知を登録する関数。"""
    @bot.tree.command(name="send_update", description="taka_1127しか使えません")
    async def send_update(interaction: discord.Interaction, password: str):
        if password != ADMIN_PASSWORD:
            await interaction.response.send_message("権限がありません。正しいパスワードを入力してください。", ephemeral=True)
            return

        try:
            # 更新通知を送信
            await notify_update(bot)
            await interaction.response.send_message("更新通知を送信しました。", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message("更新通知の送信中にエラーが発生しました。", ephemeral=True)
            print(f"エラー: {e}")