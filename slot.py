import discord
from discord.ext import commands
import random
import asyncio

# Symbols for slot machine
EMOJIS = ["🍒", ":seven:", "🍊", "🍉", "🔔", ":BAR:"]
JACKPOT_SYMBOL = ":seven:"
JACKPOT_EXTRA_SYMBOLS = [
    "⬜", ":BAR:", ":DOBBLEBAR:", ":TRIPLEBAR:", "🔴", "🔵", "🤡"
]  # For jackpot bonus


class Slot(commands.Cog):
    """
    Slot machine with integrated jackpot sequence.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="slot",
                      help="Play the slot machine (Jackpot included)")
    async def slot(self, ctx):
        """
        Slot machine main command. Includes jackpot handling if 777 is rolled.
        """
        # Initial setup
        slot_display = ["❓", "❓", "❓"]  # Placeholder for spinning effect
        message = await ctx.send(f"`{' | '.join(slot_display)}` Spinning...")

        # Simulate slot spinning for 3 seconds
        for _ in range(10):  # 3 seconds with ~10 iterations
            slot_display = [random.choice(EMOJIS) for _ in range(3)]
            await message.edit(
                content=f"`{' | '.join(slot_display)}` Spinning...")
            await asyncio.sleep(0.3)

        # Final slot result
        final_result = [random.choice(EMOJIS) for _ in range(3)]
        await message.edit(
            content=f"`{' | '.join(final_result)}` Final result!")

        # Jackpot trigger check
        if final_result == [JACKPOT_SYMBOL, JACKPOT_SYMBOL, JACKPOT_SYMBOL]:
            await self.jackpot(ctx)

        elif len(set(final_result)) == 1:  # Normal big win (non-777 matching)
            await ctx.send(
                f"✨ **JACKPOT** ✨\n`{' | '.join(final_result)}`")
        else:
            await ctx.send("**24時間後で会おう！**")

    async def jackpot(self, ctx):
        """
        Handles the jackpot sequence when 777 is rolled.
        """
        # Initialize jackpot slots
        slots_bottom = ["⬜", "⬜", "⬜"]
        slot_top = "⬜"  # Placeholder for the top slot
        message = await ctx.send(
            f"`{' | '.join(slots_bottom)}`\n`     {slot_top}     `\nJackpot spinning..."
        )

        # Spin slots for jackpot
        for _ in range(10):  # 2 seconds with ~10 iterations
            slots_bottom = [
                random.choice(JACKPOT_EXTRA_SYMBOLS) for _ in range(3)
            ]
            slot_top = random.choice(JACKPOT_EXTRA_SYMBOLS)
            await message.edit(
                content=
                f"`{' | '.join(slots_bottom)}`\n`     {slot_top}     `\nJackpot spinning..."
            )
            await asyncio.sleep(0.2)

        # Finalize jackpot slots
        slots_bottom = [random.choice(JACKPOT_EXTRA_SYMBOLS) for _ in range(3)]
        slot_top = random.choice(JACKPOT_EXTRA_SYMBOLS)
        await message.edit(
            content=
            f"`{' | '.join(slots_bottom)}`\n`     {slot_top}     `\nFinal jackpot results!"
        )

        # Evaluate Jackpot win condition
        if JACKPOT_EXTRA_SYMBOLS.index(slot_top) > max(
                JACKPOT_EXTRA_SYMBOLS.index(symbol)
                for symbol in slots_bottom):
            await ctx.send(
                f"🎉🎰 **JACKPOT BONUS WIN! {slot_top} beat the bottom symbols!** 🎰🎉"
            )
        else:
            await ctx.send(f"🔔 **Jackpot finished**")


async def setup(bot: commands.Bot):
    """
    Slot Cog registration.
    """
    await bot.add_cog(Slot(bot))
