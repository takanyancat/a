import discord
from discord import app_commands
from discord.ext import commands

# チケットを管理する辞書
tickets = {}


class TicketCreateView(discord.ui.View):

    def __init__(self, button_label, mention_roles):
        super().__init__(timeout=None)  # タイムアウトなし
        self.button_label = button_label  # ボタンラベル
        self.mention_roles = mention_roles  # メンションされるロール

    @discord.ui.button(label="チケットを作成", style=discord.ButtonStyle.primary)
    async def create_ticket(self, interaction: discord.Interaction,
                            button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user

        # チケットがすでに存在するか確認
        if user.id in tickets:
            await interaction.response.send_message("既にチケットが開かれています！",
                                                    ephemeral=True)
            return

        # チケット用のチャンネルを作成
        overwrites = {
            guild.default_role:
            discord.PermissionOverwrite(view_channel=False),
            user:
            discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.me:
            discord.PermissionOverwrite(view_channel=True)
        }
        ticket_channel = await guild.create_text_channel(
            name=f"ticket-{user.name}", overwrites=overwrites)
        tickets[user.id] = ticket_channel.id

        # チケットチャンネルにCLOSEボタンを表示
        view = CloseButtonView(ticket_channel, user.id)
        embed = discord.Embed(
            title="🎫 チケット",
            description=f"{user.mention} チケットが作成されました！サポートが必要な内容を記入してください。",
            color=discord.Color.green())
        embed.set_footer(text="CLOSEボタンを押してチケットを閉じることができます。")
        await ticket_channel.send(embed=embed, view=view)

        # ロールをメンション
        if self.mention_roles:
            mentions = " ".join([role.mention for role in self.mention_roles])
            await ticket_channel.send(f"{mentions}")

        # ユーザーにのみ見えるメッセージを送信
        await interaction.response.send_message(
            f"チケットを作成しました: {ticket_channel.mention}", ephemeral=True)


class CloseButtonView(discord.ui.View):

    def __init__(self, ticket_channel, user_id):
        super().__init__(timeout=None)  # タイムアウトなし
        self.ticket_channel = ticket_channel
        self.user_id = user_id

    @discord.ui.button(label="CLOSE", style=discord.ButtonStyle.danger)
    async def close_ticket(self, interaction: discord.Interaction,
                           button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("この操作を行う権限がありません。",
                                                    ephemeral=True)
            return

        # 確認メッセージを送信
        await interaction.response.send_message("本当にチケットを閉じますか？",
                                                view=CloseConfirmationView(
                                                    self.ticket_channel,
                                                    self.user_id),
                                                ephemeral=True)


class CloseConfirmationView(discord.ui.View):

    def __init__(self, ticket_channel, user_id):
        super().__init__(timeout=60)  # タイムアウトを60秒に設定
        self.ticket_channel = ticket_channel
        self.user_id = user_id

    @discord.ui.button(label="閉じる", style=discord.ButtonStyle.danger)
    async def confirm_close(self, interaction: discord.Interaction,
                            button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("この操作を行う権限がありません。",
                                                    ephemeral=True)
            return

        # チケットを閉じる処理
        ticket_channel_id = tickets.pop(self.user_id, None)
        if ticket_channel_id:
            channel = interaction.guild.get_channel(ticket_channel_id)
            if channel:
                await channel.delete()
                await interaction.response.send_message("チケットを閉じました！",
                                                        ephemeral=True)
            else:
                await interaction.response.send_message(
                    "チケットチャンネルが見つかりませんでした。", ephemeral=True)
        else:
            await interaction.response.send_message("チケットが見つかりませんでした。",
                                                    ephemeral=True)

    @discord.ui.button(label="閉じない", style=discord.ButtonStyle.secondary)
    async def cancel_close(self, interaction: discord.Interaction,
                           button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("この操作を行う権限がありません。",
                                                    ephemeral=True)
            return

        await interaction.response.send_message("チケットの閉鎖をキャンセルしました。",
                                                ephemeral=True)


async def setup_ticket(bot: discord.Client):

    @bot.tree.command(name="ticket", description="チケット作成用ログ配置")
    @app_commands.describe(title="チケットログのタイトル",
                           description="ログに表示される説明",
                           button_label="チケット作成ボタンのラベル",
                           mention_roles="メンションするロールを任意で選択")
    @app_commands.checks.has_permissions(administrator=True)
    async def ticket_setup(interaction: discord.Interaction,
                           title: str,
                           description: str,
                           button_label: str,
                           mention_roles: discord.Role = None):
        """
        固定メッセージを作成し、チケット作成インターフェースを表示
        """

        roles = mention_roles if isinstance(mention_roles,
                                            list) else [mention_roles]
        if len(roles) > 5:
            await interaction.response.send_message("任意でロールを選択してください！",
                                                    ephemeral=True)
            return

        embed = discord.Embed(title=title,
                              description=description,
                              color=0x72C3FC)
        embed.set_footer(text="チケットを作成するには、以下のボタンをクリックしてください。")
        view = TicketCreateView(button_label, roles)
        await interaction.response.send_message(embed=embed,
                                                view=view,
                                                ephemeral=False)
