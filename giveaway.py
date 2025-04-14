import discord
from discord import app_commands
import random
import re
import asyncio

class GiveawayView(discord.ui.View):
    def __init__(self, bot, duration_seconds, winners, product_name, product_description):
        super().__init__(timeout=None)  # Disable the default timeout for the View
        self.bot = bot
        self.duration_seconds = duration_seconds
        self.winners = winners
        self.product_name = product_name
        self.product_description = product_description
        self.participants = set()
        self.message = None
        self.embed = None  # Store the embed object for updates

    @discord.ui.button(label="参加", style=discord.ButtonStyle.green)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.participants:
            await interaction.response.send_message("既に抽選に参加しています！", ephemeral=True)
            return

        self.participants.add(interaction.user.id)
        await interaction.response.send_message("抽選に参加しました！", ephemeral=True)

    async def start_timer(self, channel):
        """
        Starts the countdown timer and updates the pinned embed message dynamically.
        """
        for remaining in range(self.duration_seconds, 0, -1):
            # Update the pinned embed message with the remaining time
            if self.message:
                self.embed.set_field_at(
                    index=0,
                    name="残り時間",
                    value=f"{remaining}秒",
                    inline=False
                )
                await self.message.edit(embed=self.embed)
            await asyncio.sleep(1)

        # Announce winners when the countdown ends
        await self.announce_winners(channel)

    async def announce_winners(self, channel):
        """
        Announces the winners once the timer is complete.
        """
        if not self.participants:
            if self.message:
                self.embed.description = "参加者がいなかったため、抽選は終了しました。"
                self.embed.clear_fields()
                await self.message.edit(embed=self.embed, view=None)
            return

        winner_count = min(self.winners, len(self.participants))
        winners = random.sample(self.participants, winner_count)
        winner_mentions = [f"<@{winner_id}>" for winner_id in winners]

        if self.message:
            self.embed.description = (
                f"🎉 **抽選終了！** 🎉\n"
                f"**景品:** {self.product_name}\n"
                f"**説明:** {self.product_description}\n"
                f"**当選者:** {', '.join(winner_mentions)}"
            )
            self.embed.clear_fields()
            await self.message.edit(embed=self.embed, view=None)

        # Notify the channel about the winners
        await channel.send(
            f"🎊 抽選が終了しました！おめでとうございます！ 🎊\n**当選者:** {', '.join(winner_mentions)}"
        )


def parse_duration(duration_str):
    """
    Parses a duration string (e.g., "2d5h3m10s") into seconds.
    """
    duration_pattern = re.compile(r"((?P<days>\d+)d)?((?P<hours>\d+)h)?((?P<minutes>\d+)m)?((?P<seconds>\d+)s)?")
    match = duration_pattern.match(duration_str)
    if not match:
        return None

    duration = match.groupdict()
    total_seconds = (
        int(duration.get("days") or 0) * 86400
        + int(duration.get("hours") or 0) * 3600
        + int(duration.get("minutes") or 0) * 60
        + int(duration.get("seconds") or 0)
    )
    return total_seconds


async def setup_giveaway(bot: discord.Client):
    @bot.tree.command(name="giveaway", description="抽選を開始します")
    @app_commands.describe(
        duration="抽選時間（例: 1d5h10m)",
        winners="当選者数",
        product_name="商品の名前",
        product_description="商品の簡易説明"
    )
    async def giveaway(
        interaction: discord.Interaction,
        duration: str,
        winners: int,
        product_name: str,
        product_description: str
    ):
        # Validate input duration
        duration_seconds = parse_duration(duration)
        if not duration_seconds or duration_seconds < 1:
            await interaction.response.send_message(
                "抽選時間は正しい形式で入力してください (例: 1d5h10m)。", ephemeral=True
            )
            return

        if winners < 1:
            await interaction.response.send_message(
                "当選者数は1以上である必要があります。", ephemeral=True
            )
            return

        # Create Giveaway View
        view = GiveawayView(bot, duration_seconds, winners, product_name, product_description)

        # Create Embed
        embed = discord.Embed(
            title="🎉 抽選開始！ 🎉",
            description=(
                f"**景品:** {product_name}\n"
                f"**説明:** {product_description}\n"
                f"**当選者数:** {winners}人\n\n"
                f"参加するには下のボタンを押してください！"
            ),
            color=discord.Color.green()
        )
        embed.add_field(name="残り時間", value=f"{duration_seconds}秒", inline=False)

        # Send and pin the giveaway message
        view.message = await interaction.channel.send(embed=embed, view=view)
        view.embed = embed  # Associate the embed with the view for dynamic updates
        await view.message.pin()

        # Start the countdown timer
        await view.start_timer(interaction.channel)

        # Respond to the command
        await interaction.response.send_message("抽選が開始されました！", ephemeral=True)