import os
import discord
from discord.ext import commands
import random
import asyncio
from pydub import AudioSegment


class Utility(commands.Cog, name="Utility"):
    """Useful commands."""

    def __init__(self, bot):
        self.bot = bot
        self.active_timers = {}  # Dictionary to keep track of active timers

    @commands.command(name="roll")
    async def roll(self, ctx, words: str):
        """Rolls a dice, .roll [number]d[sides]."""
        stripped_words = words.replace(" ", "")
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
            f"You rolled {amount} {sides}-sided dice.\nYour rolls are: "
            + ", ".join(finalRoll)
        )
        await ctx.send(finalString)

    def rollDice(self, amount, sides):
        rolls = []
        for i in range(amount):
            rolls.append(str(random.randint(1, sides)))
        return rolls

    @commands.command(name="timer")
    async def timer(
        self, ctx, words: str, *, description: str = "No description provided."
    ):
        """Set a timer for hh:mm:ss or ss with an optional description."""
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

        timer_id = len(self.active_timers) + 1  # Unique ID for the timer
        self.active_timers[timer_id] = {
            "description": description,
            "remaining_time": total_seconds,
            "user": ctx.author,
        }

        await ctx.send(
            f"{ctx.author.mention}, timer set for {hours}h {minutes}m {seconds}s! Description: {description}"
        )

        while self.active_timers.get(timer_id):
            if total_seconds <= 0:
                break
            await asyncio.sleep(1)
            total_seconds -= 1
            self.active_timers[timer_id]["remaining_time"] = total_seconds

        if timer_id in self.active_timers:
            if (
                ctx.author.voice
                and ctx.author.voice.channel
                and not ctx.guild.voice_client
            ):
                try:
                    voice_channel = ctx.author.voice.channel
                    audio_file = "./sounds/alert.mp3"
                    sound = AudioSegment.from_file(audio_file)
                    audio_duration = sound.duration_seconds

                    vc = await voice_channel.connect()
                    vc.play(discord.FFmpegPCMAudio(audio_file))

                    await ctx.send(
                        f"{ctx.author.mention}, time's up! {self.active_timers[timer_id]['description']}"
                    )
                    await asyncio.sleep(audio_duration)
                    await vc.disconnect()
                except Exception as e:
                    print(f"An error occurred: {e}")
            else:
                await ctx.send(
                    f"{ctx.author.mention}, time's up! {self.active_timers[timer_id]['description']}"
                )

            del self.active_timers[timer_id]  # Remove the timer after it has finished

    @commands.command(name="timers")
    async def timers(self, ctx):
        """List all active timers."""
        if not self.active_timers:
            await ctx.send("No active timers.")
            return

        timer_list = []
        for timer_id, timer_info in self.active_timers.items():
            remaining_time = timer_info["remaining_time"]
            hours, remainder = divmod(remaining_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            timer_list.append(
                f"**Timer {timer_id}**: {timer_info['description']} - {hours}h {minutes}m {seconds}s remaining."
            )

        await ctx.send("\n".join(timer_list))

    @commands.command(name="play")
    async def play(self, ctx):
        """Play an MP3 file uploaded with the command."""
        await ctx.send(f"{ctx.author.mention}, please upload an mp3 file.")

        def check(msg):
            return (
                msg.author == ctx.author
                and msg.channel == ctx.channel
                and msg.attachments
            )

        try:
            msg = await self.bot.wait_for("message", timeout=60.0, check=check)

            for attachment in msg.attachments:
                if attachment.filename.endswith(".mp3"):
                    audio_file = f"./sounds/{attachment.filename}"
                    await attachment.save(audio_file)

                    if ctx.author.voice and ctx.author.voice.channel:
                        voice_channel = ctx.author.voice.channel
                        vc = await voice_channel.connect()

                        sound = AudioSegment.from_file(audio_file)
                        audio_duration = sound.duration_seconds

                        vc.play(discord.FFmpegPCMAudio(audio_file))
                        await asyncio.sleep(audio_duration)

                        await vc.disconnect()

                        os.remove(audio_file)
                    else:
                        await ctx.send("You need to be in a VC to play audio.")
                    return

            await ctx.send("Please upload a valid .mp3 file.")
        except asyncio.TimeoutError:
            await ctx.send("You took too long! Please try again.")


# Add this cog to the bot
async def setup(bot):
    await bot.add_cog(Utility(bot))
