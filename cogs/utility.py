import discord
from discord.ext import commands
import random
import asyncio
from pydub import AudioSegment


class Utility(commands.Cog, name="Utility"):
    """Useful commands."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="roll")
    async def roll(self, ctx, words: str):
        """Rolls a dice, .roll [number]d[sides]."""
        stripped_words = words.replace(" ", "")
        print(stripped_words)
        if "d" in stripped_words:
            amount = 1
            sides = 1
            split = stripped_words.split("d")
            if split[0] != "":
                try:
                    amount = int(split[0])
                    sides = int(split[1])
                except ValueError:
                    await ctx.send(
                        "Wrong format, did you forget to write numbers?", delete_after=5
                    )
                    return
            else:
                try:
                    sides = int(split[1])
                except ValueError:
                    await ctx.send(
                        "Wrong format, did you forget to write numbers?", delete_after=5
                    )
                    return
        else:
            await ctx.send(
                "Wrong format, did you write [number]d[sides]?", delete_after=5
            )
            return

        if amount > 100 or sides > 1000:
            await ctx.send("Please, try smaller numbers.", delete_after=5)
            return

        finalRoll = Utility.rollDice(self, amount, sides)
        finalString = (
            f"You rolled {amount} {sides}-sided dice."
            + "\n"
            + "Your rolls are: "
            + ", ".join(finalRoll)
        )

        await ctx.send(finalString)

    def rollDice(self, amount, sides):
        rolls = []
        for i in range(amount):
            rolls.append(str(random.randint(1, sides)))
        return rolls

    @commands.command(name="timer")
    async def timer(self, ctx, words: str):
        """Set a timer for hh:mm:ss or ss."""
        await ctx.message.delete()
        split_words = words.split(":")
        hours, minutes, seconds = 0, 0, 0
        if len(split_words) == 3:
            try:
                hours = int(split_words[0])
                minutes = int(split_words[1])
                seconds = int(split_words[2])
            except ValueError:
                await ctx.send("Wrong format, did you forget to write numbers?")
                return
        else:
            try:
                seconds = int(words)
            except ValueError:
                await ctx.send("Wrong format, please write hh:mm:ss or ss.")
                return

        total_seconds = hours * 3600 + minutes * 60 + seconds
        if total_seconds <= 0:
            await ctx.send("Please set a positive duration for the timer.")
            return

        await ctx.send(
            f"{ctx.author.mention}, timer set for {hours}h {minutes}m {seconds}s!"
        )
        await asyncio.sleep(total_seconds)

        if ctx.author.voice and ctx.author.voice.channel:
            try:
                voice_channel = ctx.author.voice.channel

                audio_file = "./sounds/alert.mp3"
                sound = AudioSegment.from_file(audio_file)
                audio_duration = sound.duration_seconds

                vc = await voice_channel.connect()
                vc.play(discord.FFmpegPCMAudio(audio_file))

                await ctx.send(
                    f"{ctx.author.mention}, time's up! {hours}h {minutes}m {seconds}s have passed."
                )

                await asyncio.sleep(audio_duration)
                await vc.disconnect()
            except Exception as e:
                print(f"An error occured: {e}")
                # await ctx.send(f"An error occured: {e}")
        else:
            await ctx.send(
                f"{ctx.author.mention}, time's up! {hours}h {minutes}m {seconds}s have passed."
            )


# Add this cog to the bot
async def setup(bot):
    await bot.add_cog(Utility(bot))
