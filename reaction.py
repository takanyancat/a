import discord
from discord.ext import commands
from discord import app_commands

# リアクション管理辞書
reactions = {}


class ReactionManageView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)  # タイムアウトなし

    @discord.ui.button(label="追加", style=discord.ButtonStyle.primary)
    async def add_button(self, interaction: discord.Interaction,
                         button: discord.ui.Button):
        """
        「追加」ボタンを押したときにモーダルフォームを表示する。
        """
        modal = ReactionAddModal(interaction)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="削除", style=discord.ButtonStyle.danger)
    async def delete_button(self, interaction: discord.Interaction,
                            button: discord.ui.Button):
        """
        「削除」ボタンを押したときに削除候補を表示する。
        """
        if not reactions:
            await interaction.response.send_message("現在、設定されているリアクションはありません。",
                                                    ephemeral=True)
            return

        # 削除用の選択ビューを表示
        view = ReactionDeleteView()
        await interaction.response.send_message("削除するリアクションを選択してください。",
                                                ephemeral=True,
                                                view=view)


class ReactionAddModal(discord.ui.Modal, title="リアクション追加設定"):
    """
    リアクション追加用のモーダル（フォーム）。
    ユーザーが絵文字とチャンネル情報を入力できるようにする。
    """

    emoji = discord.ui.TextInput(label="リアクションの絵文字を入力してください (例: 😊)",
                                 style=discord.TextStyle.short,
                                 placeholder="例: 😊")
    channel_name = discord.ui.TextInput(label="対象チャンネル名を入力してください (例: general)",
                                        style=discord.TextStyle.short,
                                        placeholder="例: general")

    def __init__(self, interaction: discord.Interaction):
        super().__init__()
        self.interaction = interaction

    async def on_submit(self, interaction: discord.Interaction):
        emoji = self.emoji.value.strip()
        channel_name = self.channel_name.value.strip()

        # チャンネル確認
        target_channel = discord.utils.get(interaction.guild.text_channels,
                                           name=channel_name)
        if not target_channel:
            await interaction.response.send_message(
                f"チャンネル `{channel_name}` が見つかりませんでした。", ephemeral=True)
            return

        # リアクション設定を保存
        reactions[channel_name] = emoji
        await interaction.response.send_message(
            f"チャンネル `{channel_name}` にリアクション `{emoji}` を設定しました！",
            ephemeral=True)


class ReactionDeleteView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

        # 選択肢オプションを動的に生成
        self.add_item(self.create_select())

    def create_select(self):
        """
        選択オプションを動的に生成する関数。
        """
        options = [
            discord.SelectOption(label=channel_name,
                                 description=f"リアクション: {emoji}")
            for channel_name, emoji in reactions.items()
        ]
        return discord.ui.Select(placeholder="削除するリアクションを選択してください",
                                 options=options,
                                 custom_id="reaction_select")

    @discord.ui.select(placeholder="削除するリアクションを選択してください")
    async def reaction_select(self, interaction: discord.Interaction,
                              select: discord.ui.Select):
        selected_channel = select.values[0]

        # リアクション設定を削除
        if selected_channel in reactions:
            del reactions[selected_channel]
            await interaction.response.send_message(
                f"チャンネル `{selected_channel}` のリアクションを削除しました！", ephemeral=True)
        else:
            await interaction.response.send_message(f"選択されたリアクションが存在しません。",
                                                    ephemeral=True)


class ReactionCog(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """
        メッセージが送信されたときにリアクションを自動付与する処理。
        """
        if message.author.bot:
            return

        reaction_emoji = reactions.get(message.channel.name)
        if reaction_emoji:
            try:
                await message.add_reaction(reaction_emoji)
            except discord.HTTPException:
                print(f"絵文字 `{reaction_emoji}` をリアクションとして追加できませんでした。")


async def setup(bot: commands.Bot):
    """
    Reaction CogをBotに登録し、リアクション管理コマンドを設定する。
    """

    @bot.tree.command(name="manage_reaction", description="リアクションを管理します")
    async def manage_reaction(interaction: discord.Interaction):
        view = ReactionManageView()
        await interaction.response.send_message("リアクションの管理を開始します。",
                                                ephemeral=True,
                                                view=view)

    await bot.add_cog(ReactionCog(bot))
