import os
import re
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
        self.current_song = None  # Track currently playing song

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

    async def play_next_in_queue(self, ctx):
        """Play the next song in the queue."""
        if self.queue:
            next_song = self.queue.pop(0)
            self.current_song = next_song
            self.vc.play(
                discord.FFmpegPCMAudio(next_song),
                after=lambda e: asyncio.run_coroutine_threadsafe(
                    self.on_song_end(ctx=ctx), self.bot.loop
                ),
            )
            await ctx.send(f"Playing **{next_song[9:-4]}**.")
            self.is_playing = True
        else:
            self.is_playing = False  # Queue empty, stop playing

    async def on_song_end(self, ctx):
        """Callback when a song ends; plays the next song if available."""
        os.remove(self.current_song)  # Clean up current song file
        if self.queue:
            await self.play_next_in_queue(ctx=ctx)
        else:
            await ctx.send("Nothing else in the queue, leaving.")
            await self.cleanup()  # Disconnect if queue is empty

    async def cleanup(self):
        """Disconnect from the voice channel and reset playback state."""
        if self.vc:
            await self.vc.disconnect()
            self.vc = None
            self.is_playing = False
            self.current_song = None

    @commands.command(name="ytplay")
    async def ytplay(self, ctx, url: str):
        """Download and add audio to queue from a YouTube URL."""
        if not await self.ensure_voice(ctx):
            return

        # Define download limits
        max_size = 100 * 1024 * 1024  # 100MB size limit
        max_length = 600  # 10 minutes length limit

        try:
            # Fetch video info
            with yt_dlp.YoutubeDL({"format": "bestaudio/best", "quiet": True}) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                video_title = self.sanitize_filename(
                    info_dict.get("title", "downloaded_audio")
                )
                file_name = f"{video_title}.mp3"
                file_path = os.path.join("./sounds", file_name)
                if info_dict["duration"] > max_length:
                    await ctx.send("Video too long to download.")
                    return
                if info_dict.get("filesize", 0) > max_size:
                    await ctx.send("File too large to download.")
                    return

            await ctx.send(f"Downloading **{video_title}**...")

            # Download options
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

            # Download audio
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            # Handle double-extension issue
            if not os.path.exists(file_path) and os.path.exists(file_path + ".mp3"):
                os.rename(file_path + ".mp3", file_path)

            # Add to queue and notify
            self.queue.append(file_path)
            await ctx.send(f"**{video_title}** added to the queue.")

            if not self.is_playing:
                await self.play_next_in_queue(ctx=ctx)

        except Exception as e:
            await ctx.send(f"An error occurred while downloading: {e}")

    def sanitize_filename(self, filename):
        """Remove special characters from filename for compatibility."""
        return re.sub(r"[^\w\s-]", "", filename).strip()

    @commands.command(name="queue")
    async def show_queue(self, ctx):
        """Display the current queue."""
        if self.queue:
            queue_list = "\n".join(
                [
                    f"{i + 1}. {os.path.basename(song)}"
                    for i, song in enumerate(self.queue)
                ]
            )
            await ctx.send(f"**Current Queue:**\n{queue_list}")
        else:
            await ctx.send("The queue is empty.")

    @commands.command(name="skip")
    async def skip(self, ctx):
        """Skip the currently playing song."""
        if self.vc and self.vc.is_playing():
            self.vc.stop()
            # await asyncio.sleep(2)
            await ctx.send("Skipped the current song.")
            # await self.on_song_end(ctx=ctx)

    @commands.command(name="stop")
    async def stop(self, ctx):
        """Stop playback and clear the queue."""
        if self.vc:
            if self.queue:
                for song in self.queue:
                    try:
                        os.remove(song)  # Remove each song in the queue
                    except FileNotFoundError:
                        pass
            self.queue.clear()
            self.vc.stop()
            self.is_playing = False
            await ctx.send("Playback stopped, and the queue has been cleared.")
            await self.cleanup()

    @commands.command(name="pause")
    async def pause(self, ctx):
        """Pause the currently playing song."""
        if self.vc and self.vc.is_playing():
            self.vc.pause()
            await ctx.send("Playback paused.")
        else:
            await ctx.send("There is no audio currently playing to pause.")

    @commands.command(name="resume")
    async def resume(self, ctx):
        """Resume the currently paused song."""
        if self.vc and self.vc.is_paused():
            self.vc.resume()
            await ctx.send("Playback resumed.")
        else:
            await ctx.send("There is no audio currently paused to resume.")


async def setup(bot):
    await bot.add_cog(AudioPlayer(bot))
