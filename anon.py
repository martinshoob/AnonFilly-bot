import os
import discord
import asyncio
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = str(os.getenv("DISCORD_TOKEN"))

# Set up intents
intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent

# Define bot with prefix
bot = commands.Bot(command_prefix=".", intents=intents)


@bot.event
async def on_ready():
    print(f"{bot.user} is ready!")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="REEEEEEEEEEE"))


async def load_cogs():
    await bot.load_extension("cogs.management")
    await bot.load_extension("cogs.fun")
    await bot.load_extension("cogs.utility")
    await bot.load_extension("cogs.audio_player")


async def main():
    await load_cogs()
    await bot.start(TOKEN)


asyncio.run(main())
