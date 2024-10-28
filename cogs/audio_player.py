import os
import discord
from discord.ext import commands
import asyncio
import yt_dlp


class AudioPlayer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = []  # Queue to store file paths of songs
        self.is_playing = False  # Track if something is currently playing
        self.vc = None  # Voice client

    async def ensure_voice(self, ctx):
        """Ensure the bot is in the user's voice channel."""
        if ctx.author.voice and ctx.author.voice.channel:
            if ctx.guild.voice_client is None:
                self.vc = await ctx.author.voice.channel.connect()
            else:
                self.vc = ctx.guild.voice_client
            return True
        await ctx.send("You need to be in a voice channel to play audio.")
        return False

    async def play_next_in_queue(self):
        """Play the next song in the queue."""
        if self.queue:
            next_song = self.queue.pop(0)
            self.vc.play(
                discord.FFmpegPCMAudio(next_song),
                after=lambda e: asyncio.run_coroutine_threadsafe(
                    self.on_song_end(), self.bot.loop
                ),
            )
            self.is_playing = True
        else:
            self.is_playing = False  # Queue is empty, stop playing

    async def on_song_end(self):
        """Callback when a song ends; plays the next song if available."""
        await asyncio.sleep(1)  # Delay to ensure current song cleanup
        if not self.queue:
            await self.vc.disconnect()  # Disconnect if the queue is empty
            self.vc = None
        else:
            await self.play_next_in_queue()

    @commands.command(name="ytplay")
    async def ytplay(self, ctx, url: str):
        """Download and add audio to queue from a YouTube URL."""
        if not await self.ensure_voice(ctx):
            return

        # Download audio and add it to the queue
        output_dir = "./sounds"
        os.makedirs(output_dir, exist_ok=True)

        # Extract video info to determine file name
        try:
            with yt_dlp.YoutubeDL({"format": "bestaudio/best", "quiet": True}) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                video_title = info_dict.get("title", "downloaded_audio").replace(
                    " ", "_"
                )
                file_name = f"{video_title}.mp3"
                file_path = os.path.join(output_dir, file_name)
        except Exception as e:
            await ctx.send(f"Error fetching video info: {e}")
            return

        # Download the audio
        try:
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": file_path,
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ],
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            # Check if extra extension needs to be fixed
            if not os.path.exists(file_path) and os.path.exists(file_path + ".mp3"):
                os.rename(file_path + ".mp3", file_path)

            # Add the downloaded file to the queue
            self.queue.append(file_path)
            await ctx.send(f"**{video_title}** added to the queue.")

            # Play if not currently playing
            if not self.is_playing:
                await self.play_next_in_queue()

        except Exception as e:
            await ctx.send(f"An error occurred while downloading: {e}")

    @commands.command(name="skip")
    async def skip(self, ctx):
        """Skip the currently playing song."""
        if self.vc and self.vc.is_playing():
            self.vc.stop()
            await ctx.send("Skipped the current song.")
            await self.on_song_end()

    @commands.command(name="queue")
    async def show_queue(self, ctx):
        """Display the current queue."""
        if self.queue:
            queue_list = "\n".join(
                [
                    f"{i+1}. {os.path.basename(song)}"
                    for i, song in enumerate(self.queue)
                ]
            )
            await ctx.send(f"**Current Queue:**\n{queue_list}")
        else:
            await ctx.send("The queue is empty.")

    @commands.command(name="stop")
    async def stop(self, ctx):
        """Stop playback and clear the queue."""
        if self.vc:
            self.queue.clear()  # Clear the queue
            self.vc.stop()  # Stop any currently playing song
            self.is_playing = False
            await ctx.send("Playback stopped, and the queue has been cleared.")
            await self.vc.disconnect()  # Disconnect from the voice channel
            self.vc = None

    @commands.command(name="clearqueue")
    async def clearqueue(self, ctx):
        """Clear the current queue without stopping playback."""
        if self.queue:
            self.queue.clear()
            await ctx.send("Queue has been cleared.")
        else:
            await ctx.send("The queue is already empty.")


# Add this cog to the bot
async def setup(bot):
    await bot.add_cog(AudioPlayer(bot))
