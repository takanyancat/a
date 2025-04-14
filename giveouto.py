import discord
from discord import app_commands
import random
import asyncio

class GiveawayView(discord.ui.View):
    def __init__(self, bot, title, prize_list, winners_count, duration_seconds):
        super().__init__(timeout=None)  # Disable automatic timeout for the View
        self.bot = bot
        self.title = title
        self.prize_list = prize_list
        self.winners_count = winners_count
        self.participants = set()
        self.message = None
        self.duration_seconds = duration_seconds  # Countdown timer duration
        self.embed = None  # The embed object for dynamic updates

    @discord.ui.button(label="参加", style=discord.ButtonStyle.success)
    async def join_giveaway(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        if user.id not in self.participants:
            self.participants.add(user.id)
            await interaction.response.send_message(f"{user.mention} が抽選に参加しました！", ephemeral=True)
        else:
            await interaction.response.send_message("すでに参加しています！", ephemeral=True)

    async def start_timer(self):
        """
        Dynamically update the embed with the remaining time every second.
        """
        for remaining in range(self.duration_seconds, 0, -1):
            if self.message:
                self.embed.set_field_at(
                    index=0,
                    name="残り時間",
                    value=f"{remaining}秒",
                    inline=False
                )
                await self.message.edit(embed=self.embed)
            await asyncio.sleep(1)

        # Time is up, announce winners
        await self.announce_winners()

    async def announce_winners(self):
        """
        Announces the winners and sends DM notifications to each winner with their prize.
        """
        if not self.participants:
            # No participants
            if self.message:
                self.embed.description = "⏳ 抽選に参加者がいなかったため、終了しました。"
                self.embed.clear_fields()
                await self.message.edit(embed=self.embed, view=None)
            return

        winners = random.sample(self.participants, min(self.winners_count, len(self.participants)))
        winner_mentions = [f"<@{winner_id}>" for winner_id in winners]

        # Update the embed with winners
        if self.message:
            self.embed.description = (
                f"🎉 **抽選終了！** 🎉\n"
                f"**タイトル:** {self.title}\n"
                f"**当選者:** {', '.join(winner_mentions)}\n"
                f"**景品:** {', '.join(self.prize_list[:len(winners)])}"
            )
            self.embed.clear_fields()
            await self.message.edit(embed=self.embed, view=None)

        # Send DM to winners
        for winner_id, prize in zip(winners, self.prize_list):
            winner = self.bot.get_user(winner_id)
            if winner:
                try:
                    dm_embed = discord.Embed(
                        title="🎁 抽選当選おめでとうございます！",
                        description=(
                            f"**タイトル:** {self.title}\n"
                            f"**景品:** {prize}\n"
                            f"このメッセージは自動送信です。おめでとうございます！"
                        ),
                        color=discord.Color.blue()
                    )
                    await winner.send(embed=dm_embed)
                except discord.Forbidden:
                    await self.message.channel.send(
                        f"{winner.mention} にDMを送信できませんでした。DMを有効にしてください。"
                    )


async def setup_giveouto(bot: discord.Client):
    @bot.tree.command(name="giveouto", description="抽選を開始します")
    @app_commands.describe(
        duration="抽選時間（分）",
        winners="当選者数",
        title="抽選のタイトル",
        prizes="配布物のリスト（カンマ区切り）"
    )
    async def giveouto(
        interaction: discord.Interaction,
        duration: int,
        winners: int,
        title: str,
        prizes: str
    ):
        # Validate input
        if duration < 1 or winners < 1:
            await interaction.response.send_message(
                "抽選時間と当選者数は1以上である必要があります。",
                ephemeral=True
            )
            return

        prize_list = [prize.strip() for prize in prizes.split(",")]

        if len(prize_list) < winners:
            await interaction.response.send_message(
                f"景品の数 ({len(prize_list)}) が当選者数 ({winners}) に足りません。",
                ephemeral=True
            )
            return

        # Create the giveaway view
        view = GiveawayView(bot, title, prize_list, winners, duration * 60)

        # Create the initial embed
        embed = discord.Embed(
            title="🎉 抽選開始！ 🎉",
            description=(
                f"**タイトル:** {title}\n"
                f"**当選者数:** {winners}人\n"
                f"**景品:** {', '.join(prize_list)}\n\n"
                f"参加するには下のボタンを押してください！"
            ),
            color=discord.Color.orange()
        )
        embed.add_field(name="残り時間", value=f"{duration * 60}秒", inline=False)

        # Send and pin the giveaway message
        view.message = await interaction.channel.send(embed=embed, view=view)
        view.embed = embed  # Link the embed to the view
        await interaction.response.send_message("抽選を開始しました！", ephemeral=True)

        # Start the countdown timer
        await view.start_timer()