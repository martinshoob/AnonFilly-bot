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
        amount = 1
        sides = 1
        if "d" in stripped_words:
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
            try:
                sides = int(words)
            except ValueError:
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
        for _ in range(amount):
            rolls.append(str(random.randint(1, sides)))
        return rolls

    @commands.group(name="timer", invoke_without_command=True)
    async def timer(self, ctx):
        """Base command for timer-related subcommands."""
        await ctx.send("Use a subcommand like start, stop, clear, extend, or list.")

    @timer.command(name="set")
    async def set_timer(
        self, ctx, time_str: str, *, description: str = "No description provided."
    ):
        """Set a timer for a specific duration in 'hh:mm:ss' or 'ss' format."""
        total_seconds = await self.parse_time(ctx, time_str)
        if total_seconds is None:
            await ctx.send("Please enter a positive duration for the timer.")
            return

        timer_id = len(self.active_timers) + 1
        self.active_timers[timer_id] = {
            "description": description,
            "remaining_time": total_seconds,
            "user": ctx.author,
        }

        hours, minutes, seconds = (
            total_seconds // 3600,
            (total_seconds % 3600) // 60,
            total_seconds % 60,
        )
        await ctx.send(
            f"{ctx.author.mention}, timer set for {hours}h {minutes}m {seconds}s! Description: {description}"
        )
        await self.run_timer(timer_id)
        await self.handle_timer_expiry(ctx, timer_id)

    @timer.command(name="stop")
    async def stop_timer(self, ctx, timer_id: int):
        """Stop a specific timer by its ID."""
        if timer_id in self.active_timers:
            description = self.active_timers[timer_id]["description"]
            del self.active_timers[timer_id]
            await ctx.send(
                f'Deleted **timer {timer_id}** with the description: "{description}"'
            )
        else:
            await ctx.send(
                "A timer with this ID doesn't exist. You can check existing timers with `.timer list`."
            )

    @timer.command(name="clear")
    async def clear_timers(self, ctx):
        """Clear all active timers."""
        timer_count = len(self.active_timers)
        self.active_timers.clear()
        await ctx.send(f"**Cleared all {timer_count} timers.**")

    @timer.command(name="extend")
    async def extend_timer(self, ctx, timer_id: int, time_str: str):
        """Extend an existing timer by a specific duration."""
        total_seconds = await self.parse_time(ctx, time_str)
        if total_seconds is None:
            await ctx.send("Invalid time provided for extending.")
            return

        if timer_id not in self.active_timers:
            await ctx.send("Timer with this ID doesn't exist.")
            return

        self.active_timers[timer_id]["remaining_time"] += total_seconds
        hours, minutes, seconds = (
            total_seconds // 3600,
            (total_seconds % 3600) // 60,
            total_seconds % 60,
        )
        await ctx.send(f"Extended timer {timer_id} by {hours}h {minutes}m {seconds}s.")

    @timer.command(name="list")
    async def list_timers(self, ctx):
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

    async def handle_timer_expiry(self, ctx, timer_id):
        """Handles actions when a timer expires."""
        if timer_id not in self.active_timers:
            return

        try:
            if (
                ctx.author.voice
                and ctx.author.voice.channel
                and not ctx.guild.voice_client
            ):
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
            else:
                await ctx.send(
                    f"{ctx.author.mention}, time's up! {self.active_timers[timer_id]['description']}"
                )
        except Exception as e:
            print(f"An error occurred while handling timer expiry: {e}")

        del self.active_timers[timer_id]

    async def run_timer(self, timer_id):
        while self.active_timers.get(timer_id):
            remaining_time = self.active_timers[timer_id]["remaining_time"]
            if remaining_time <= 0:
                break
            await asyncio.sleep(1)
            self.active_timers[timer_id]["remaining_time"] -= 1

    async def parse_time(self, ctx, time_str: str) -> int | None:
        """Parse a time string in 'hh:mm:ss', 'mm:ss', or 'ss' format to total seconds."""
        try:
            # Split time_str by colons to identify hh:mm:ss or mm:ss formats
            time_parts = list(map(int, time_str.split(":")))

            if len(time_parts) == 3:  # hh:mm:ss
                hours, minutes, seconds = time_parts
            elif len(time_parts) == 2:  # mm:ss
                hours, minutes, seconds = 0, *time_parts
            elif len(time_parts) == 1:  # ss
                hours, minutes, seconds = 0, 0, time_parts[0]
            else:
                await ctx.send(
                    "Please provide time in 'hh:mm:ss', 'mm:ss', or 'ss' format."
                )
                return None

            # Calculate total seconds
            total_seconds = hours * 3600 + minutes * 60 + seconds
            return total_seconds if total_seconds > 0 else None

        except ValueError:
            await ctx.send(
                "Invalid time format. Please use numbers only in 'hh:mm:ss', 'mm:ss', or 'ss' format."
            )
            return None

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
