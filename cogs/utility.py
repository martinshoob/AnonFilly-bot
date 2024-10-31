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

    @commands.command(name="timer")
    async def timer(
        self, ctx, words: str, *, description: str = "No description provided."
    ):
        """Set a timer for hh:mm:ss or ss with an optional description."""
        if words == "stop":
            await self.stop_timer(ctx, description)
            return

        if words == "clear":
            timer_amount = len(self.active_timers)
            for i in range(1, timer_amount+1):
                print(i)
                print(range(len(self.active_timers)))
                await self.stop_timer(ctx, i)
            await ctx.send("**Cleared all timers.**")
            return

        if words == "extend":
            await self.extend_timer(ctx, description)
            return

        if words == "list":
            await self.list_timers(ctx)
            return
            
        id_amount = await self.format(ctx, words, False)
        if id_amount is not None:
            total_seconds = id_amount[0]
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
        else:
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

        await self.run_timer(timer_id)

        #while self.active_timers.get(timer_id):
        #    if total_seconds <= 0:
        #        break
        #    await asyncio.sleep(1)
        #    total_seconds -= 1
        #    self.active_timers[timer_id]["remaining_time"] = total_seconds

        await self.handle_timer_expiry(ctx, timer_id)
        #if timer_id in self.active_timers:
        #    if (
        #        ctx.author.voice
        #        and ctx.author.voice.channel
        #        and not ctx.guild.voice_client
        #    ):
        #        try:
        #            voice_channel = ctx.author.voice.channel
        #            audio_file = "./sounds/alert.mp3"
        #            sound = AudioSegment.from_file(audio_file)
        #            audio_duration = sound.duration_seconds

        #            vc = await voice_channel.connect()
        #            vc.play(discord.FFmpegPCMAudio(audio_file))

        #            await ctx.send(
        #                f"{ctx.author.mention}, time's up! {self.active_timers[timer_id]['description']}"
        #            )
        #            await asyncio.sleep(audio_duration)
        #            await vc.disconnect()
        #        except Exception as e:
        #            print(f"An error occurred: {e}")
        #    else:
        #        await ctx.send(
        #            f"{ctx.author.mention}, time's up! {self.active_timers[timer_id]['description']}"
        #        )

        #    del self.active_timers[timer_id]  # Remove the timer after it has finished

    async def handle_timer_expiry(self, ctx, timer_id):
        """Handles actions when a timer expires."""
        if timer_id not in self.active_timers:
            return  # If the timer is not in the active timers, exit the function

        try:
            # Send message or play sound in the user's voice channel if they're connected
            if ctx.author.voice and ctx.author.voice.channel and not ctx.guild.voice_client:
                voice_channel = ctx.author.voice.channel
                audio_file = "./sounds/alert.mp3"
                
                # Load audio file and get duration
                sound = AudioSegment.from_file(audio_file)
                audio_duration = sound.duration_seconds
                
                # Connect to the voice channel and play sound
                vc = await voice_channel.connect()
                vc.play(discord.FFmpegPCMAudio(audio_file))
                
                await ctx.send(
                    f"{ctx.author.mention}, time's up! {self.active_timers[timer_id]['description']}"
                )
                await asyncio.sleep(audio_duration)  # Wait for audio to finish playing
                await vc.disconnect()
            else:
                # Send a message if voice channel connection is not possible
                await ctx.send(
                    f"{ctx.author.mention}, time's up! {self.active_timers[timer_id]['description']}"
                )
        except Exception as e:
            print(f"An error occurred while handling timer expiry: {e}")
        
        # Remove the timer after it has finished
        del self.active_timers[timer_id]

    async def run_timer(self, timer_id):
        # Run while the timer is active
        while self.active_timers.get(timer_id):
            # Access remaining time directly from the active_timers dictionary
            remaining_time = self.active_timers[timer_id]["remaining_time"]

            # Check if time is up
            if remaining_time <= 0:
                break

            # Wait for 1 second
            await asyncio.sleep(1)

            # Reduce time by 1 second in the dictionary itself
            self.active_timers[timer_id]["remaining_time"] -= 1

    async def stop_timer(self, ctx, id)->None:
        try:
            delete_id = int(id)
            # await ctx.send(delete_id)
        except ValueError:
            await ctx.send("Wrong format. Did you write a number (Timer ID)?")
            return

        try:
            await ctx.send(f"Deleted **timer {delete_id}** with the description: \"{self.active_timers[delete_id]["description"]}\"")
            del self.active_timers[delete_id]
            return
        except ValueError:
            await ctx.send("A timer with this ID doesn't exist. You can check existing timers with '.timers'.")
            return

    async def extend_timer(self, ctx, amount):
        id_amount = await self.format(ctx, amount, True)
        if id_amount is not None:
            total_seconds = id_amount[0]
            id = id_amount[1]
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
        else:
            return

        try:
            print(self.active_timers[id]["remaining_time"])
            self.active_timers[id]["remaining_time"] += total_seconds
            await ctx.send(f"Extended timer {id} by {hours}h {minutes}m {seconds}s.")
        except ValueError:
            await ctx.send("Timer with this ID doesn't exist.")
            return

    async def format(self, ctx, id_amount: str, req_id: bool) -> list | None:
        try:
            # Split the input based on space to separate ID and time
            parts = id_amount.split(" ", 1)
            
            # Initialize variables
            id = None
            time_str = ""
            
            # If req_id is True, ensure we have both an ID and a time string
            if req_id:
                if len(parts) != 2:
                    await ctx.send("Please provide both an ID and a time string in hh:mm:ss or ss format.")
                    return None
                id_str, time_str = parts
                id = int(id_str)  # Try to convert ID to an integer
            else:
                time_str = parts[0]

            # Determine if time_str is in hh:mm:ss or ss format
            if ":" in time_str:
                # Expect hh:mm:ss format with exactly 3 parts
                time_parts = time_str.split(":")
                if len(time_parts) != 3:
                    await ctx.send("Please provide the time in hh:mm:ss format.")
                    return None
                hours, minutes, seconds = map(int, time_parts)
            else:
                # Expect only seconds
                hours, minutes = 0, 0
                seconds = int(time_str)

            # Calculate total seconds
            total_seconds = hours * 3600 + minutes * 60 + seconds

            # Check for valid positive total_seconds
            if total_seconds <= 0:
                await ctx.send("Please set a positive duration for the timer.")
                return None

            # Return the result with or without ID based on req_id
            return [total_seconds, id] if req_id else [total_seconds]

        except ValueError:
            # Handle parsing errors
            await ctx.send("Invalid format. Please enter time in hh:mm:ss or ss format, and use numbers only.")
            return None


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
