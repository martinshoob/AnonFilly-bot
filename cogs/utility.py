import os
import discord
from discord.ext import commands
import random
import asyncio
import yt_dlp
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
                        print("bruh")
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

    @commands.command(name="ytplay")
    async def ytplay(self, ctx, url: str):
        """Download and play audio from a YouTube URL in MP3 format with a dynamic filename in ./sounds directory."""

        # Ensure user is in a voice channel
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("You need to be in a voice channel to play audio.")
            return

        voice_channel = ctx.author.voice.channel

        # Set output directory and ensure it exists
        output_dir = "./sounds"
        os.makedirs(output_dir, exist_ok=True)

        # Use yt-dlp to extract video metadata and generate a dynamic filename
        ydl_opts_info = {"format": "bestaudio/best", "quiet": True}

        try:
            with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                video_title = info_dict.get("title", "downloaded_audio").replace(
                    " ", "_"
                )
                temp_file_name = f"{video_title}.mp3"  # Initial filename for download
                file_path = os.path.join(output_dir, temp_file_name)
        except Exception as e:
            await ctx.send(f"An error occurred while fetching video info: {e}")
            return

        # Define yt-dlp download options with a specified filename in ./sounds
        ydl_opts_download = {
            "format": "bestaudio/best",
            "outtmpl": file_path,  # Output path in ./sounds
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
        }

        # Download audio using yt-dlp
        await ctx.send(f"Downloading **{video_title}**... This may take a moment.")

        try:
            with yt_dlp.YoutubeDL(ydl_opts_download) as ydl:
                ydl.download([url])
            await ctx.send("Audio downloaded successfully.")

            # Check if the file has an extra .mp3 extension and rename if necessary
            if not os.path.exists(file_path) and os.path.exists(file_path + ".mp3"):
                os.rename(file_path + ".mp3", file_path)

        except Exception as e:
            await ctx.send(f"An error occurred while downloading: {e}")
            return

        # Connect to the voice channel and play the audio
        try:
            # Connect to the voice channel
            if ctx.guild.voice_client is None:
                vc = await voice_channel.connect()
                await ctx.send("Bot joined the voice channel.")
            else:
                vc = ctx.guild.voice_client

            # Play the downloaded audio
            vc.play(
                discord.FFmpegPCMAudio(file_path),
                after=lambda e: print("Playback finished."),
            )

            # Wait until audio is done playing
            while vc.is_playing():
                await asyncio.sleep(1)

            # Disconnect and clean up
            await vc.disconnect()
            os.remove(file_path)
            await ctx.send(
                f"Playback finished for **{video_title}**. Bot has left the voice channel."
            )

        except discord.DiscordException as e:
            await ctx.send(f"An error occurred during playback: {e}")


# Add this cog to the bot
async def setup(bot):
    await bot.add_cog(Utility(bot))
