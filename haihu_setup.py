import discord
from discord import app_commands
from discord.ui import View, Button, Select
from collections import defaultdict

# 配布物データ管理
distribution_records = defaultdict(dict)  # {guild_id: {item_name: {details}}}
log_channels = defaultdict(lambda: None)  # {guild_id: log_channel_id}


class ReceiveButtonView(View):
    """
    受け取るボタンを表示するビュー
    """

    def __init__(self, guild_id: int, item_name: str, user_id: int):
        super().__init__(timeout=None)
        self.guild_id = guild_id
        self.item_name = item_name
        self.user_id = user_id

    @discord.ui.button(label="受け取る", style=discord.ButtonStyle.success)
    async def receive_item(self, interaction: discord.Interaction,
                           button: discord.ui.Button):
        """
        受け取るボタンの処理
        """
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("この操作は許可されていません。",
                                                    ephemeral=True)
            return

        item = distribution_records[self.guild_id].get(self.item_name)
        if item:
            # 受け取り回数をカウント
            item["receives"] += 1
            receive_count = item["receives"]

            # DMで中身を送信
            dm_message = discord.Embed(
                title="配布受け取り",
                description=(f"**商品名:** {item['name']}\n"
                             f"**説明:** {item['description']}\n"
                             f"**内容:** {item['content']}"),
                color=discord.Color.blue())
            dm_message.set_footer(text="TAKABOT | 配布受け取り完了")
            try:
                await interaction.user.send(embed=dm_message)
            except discord.Forbidden:
                await interaction.response.send_message(
                    "DMの送信に失敗しました。DM設定をご確認ください。", ephemeral=True)
                return

            # ログチャンネルに記録
            log_channel_id = log_channels.get(self.guild_id)
            if log_channel_id:
                log_channel = interaction.guild.get_channel(log_channel_id)
                if log_channel:
                    log_message = discord.Embed(
                        title="配布実績",
                        description=(
                            f"{interaction.user.mention} が配布を受け取りました！\n"
                            f"## **{receive_count}回目**の配布"),
                        color=discord.Color.green(),
                    )
                    log_message.set_thumbnail(
                        url=interaction.user.avatar.url if interaction.user.
                        avatar else None)
                    log_message.set_footer(text="配布")
                    await log_channel.send(embed=log_message)

            await interaction.response.send_message("DMに商品を送信しました！",
                                                    ephemeral=True)
        else:
            await interaction.response.send_message("指定された配布物が見つかりませんでした。",
                                                    ephemeral=True)


class HaihuSetupView(View):
    """
    配布物管理ビュー：設置または削除の操作を提供
    """

    def __init__(self, guild_id: int):
        super().__init__(timeout=None)
        self.guild_id = guild_id

    @discord.ui.button(label="削除", style=discord.ButtonStyle.danger)
    async def delete_item(self, interaction: discord.Interaction,
                          button: discord.ui.Button):
        """
        配布物を削除するボタンの処理
        """
        items = distribution_records.get(self.guild_id, {})

        if not items:
            await interaction.response.send_message("削除可能な配布物が存在しません。",
                                                    ephemeral=True)
            return

        options = [
            discord.SelectOption(label=item_name,
                                 description=item_data["description"])
            for item_name, item_data in items.items()
        ]
        view = SelectView(options, interaction.user.id, "削除", self.guild_id)
        await interaction.response.send_message("削除する配布物を選択してください。",
                                                view=view,
                                                ephemeral=True)

    @discord.ui.button(label="設置", style=discord.ButtonStyle.success)
    async def setup_item(self, interaction: discord.Interaction,
                         button: discord.ui.Button):
        """
        配布物を設置するボタンの処理
        """
        items = distribution_records.get(self.guild_id, {})

        if not items:
            await interaction.response.send_message("設置可能な配布物が存在しません。",
                                                    ephemeral=True)
            return

        options = [
            discord.SelectOption(label=item_name,
                                 description=item_data["description"])
            for item_name, item_data in items.items()
        ]
        view = SelectView(options, interaction.user.id, "設置", self.guild_id)
        await interaction.response.send_message("設置する配布物を選択してください。",
                                                view=view,
                                                ephemeral=True)


class SelectView(View):
    """
    配布物の削除または設置を選択するビュー
    """

    def __init__(self, options, user_id: int, action: str, guild_id: int):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.action = action
        self.guild_id = guild_id

        select = Select(
            placeholder=f"{action}する配布物を選択してください。",
            options=options,
            min_values=1,
            max_values=1,
        )
        select.callback = self.handle_selection
        self.add_item(select)

    async def handle_selection(self, interaction: discord.Interaction):
        """
        選択した配布物の削除または設置を処理
        """
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("この操作は許可されていません。",
                                                    ephemeral=True)
            return

        selected_option = interaction.data.get("values", [None])[0]
        if not selected_option:
            await interaction.response.send_message("選択されたアイテムが無効です。",
                                                    ephemeral=True)
            return

        if self.action == "削除":
            item = distribution_records[self.guild_id].pop(
                selected_option, None)
            if item:
                await interaction.response.send_message(
                    f"アイテム **{selected_option}** を削除しました。", ephemeral=True)
            else:
                await interaction.response.send_message("選択されたアイテムは既に存在しません。",
                                                        ephemeral=True)
        elif self.action == "設置":
            item = distribution_records[self.guild_id].get(selected_option)
            if item:
                embed = discord.Embed(
                    title="配布物",
                    description=(f"**商品名:** {item['name']}\n"
                                 f"**説明:** {item['description']}\n"
                                 f"**内容:** {item['content']}"),
                    color=discord.Color.green(),
                )
                embed.set_footer(text="受け取るボタンを押してください。")
                view = ReceiveButtonView(self.guild_id, selected_option,
                                         interaction.user.id)
                await interaction.channel.send(embed=embed, view=view)
                await interaction.response.send_message(
                    f"配布物 **{selected_option}** を設置しました。", ephemeral=True)


@app_commands.command(name="haihu_setup", description="配布物の登録と管理を行います。")
@app_commands.describe(
    name="名前",
    description="簡易説明",
    content="内容(この内容がDMに送信されます。)",
    log_channel="受け取った実績を報告するチャンネルを選択してください。",
)
async def haihu_setup(
    interaction: discord.Interaction,
    name: str,
    description: str,
    content: str,
    log_channel: discord.TextChannel,
):
    """
    配布物の登録と管理
    """
    guild_id = interaction.guild.id

    # 配布物を登録
    distribution_records[guild_id][name] = {
        "name": name,
        "description": description,
        "content": content,
        "receives": 0,
    }
    log_channels[guild_id] = log_channel.id

    embed = discord.Embed(
        title="📦 配布物が登録されました！",
        description=(f"**商品名:** {name}\n"
                     f"**説明:** {description}\n"
                     f"**内容:** {content}\n"
                     f"**ログチャンネル:** <#{log_channel.id}>"),
        color=discord.Color.green(),
    )
    await interaction.response.send_message(embed=embed)

    # 配布物管理のビューを送信
    embed_manage = discord.Embed(
        title="📦 配布物管理",
        description="登録が完了しました。操作を選択してください。",
        color=discord.Color.orange(),
    )
    view = HaihuSetupView(guild_id)
    await interaction.channel.send(embed=embed_manage, view=view)


async def setup_haihu_setup(bot: discord.Client):
    """
    コマンドをボットに登録します。
    """
    bot.tree.add_command(haihu_setup)
