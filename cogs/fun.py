import discord
from discord.app_commands import command
from discord.ext import commands
import random
import os
from discord.ext.commands.context import DeferTyping
import requests


class Fun(commands.Cog, name="Fun"):
    """Fun commands for entertainment."""

    def __init__(self, bot):
        self.bot = bot
        self.quotes_file_path = "./files/quotes.txt"  # Path to the quotes file
        # Ensure the quotes file exists
        os.makedirs(os.path.dirname(self.quotes_file_path), exist_ok=True)
        open(self.quotes_file_path, "a").close()  # Create the file if it doesn't exist

    @commands.command(name="edge")
    async def edge(self, ctx, user: discord.Member = None):
        """Edge."""
        await ctx.message.delete()
        edge_meme_url = "https://app.tradeoffgame.com/images/browsers/edge-icon.png"  # Replace with a real image URL

        embed = discord.Embed(title="Edging", color=discord.Color.blue())
        embed.set_image(url=edge_meme_url)
        # Check if a user is mentioned
        if user is not None:
            try:
                await user.send(embed=embed)  # Send embed to the user's DMs
                await ctx.send(f"Edged {user.mention}.", delete_after=5)
            except discord.Forbidden:
                await ctx.send(
                    f"Could not send the edge meme to {user.mention}. They might have DMs disabled.",
                    delete_after=5,
                )
        else:
            await ctx.send(embed=embed)  # Send embed in the current channel

    @commands.command(name="explode")
    async def explode(self, ctx, *, words: str):
        """Explodes with the given words."""
        await ctx.message.delete()
        response = f"💥 {words} 💥"  # Format the response with explosion emojis
        await ctx.send(response)

    @commands.command(name="quote")
    async def quote(self, ctx, user: discord.Member = None, *, quote: str = None):
        """Store or retrieve a quote."""
        if ctx.message.reference:  # Check if the command is a reply
            message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            quoted_user = message.author
            quote_content = message.content

            # Save the quote to the file
            self.save_quote(quoted_user.id, quote_content)
            await ctx.send(f"Quote saved for {quoted_user.mention}!")

        elif user and quote:  # For command like `!quote @user Your quote here`
            self.save_quote(user.id, quote)
            await ctx.send(f"Quote saved for {user.mention}!")

        else:  # Retrieve a random quote for the user
            if user:
                user_quotes = self.get_user_quotes(user.id)
                if user_quotes:
                    random_quote = random.choice(user_quotes)
                    await ctx.send(f'{user.mention} said: "{random_quote}"')
                else:
                    await ctx.send(f"No quotes found for {user.mention}.")
            else:
                await ctx.send(
                    "Please mention a user or reply to a message to save a quote."
                )

    def save_quote(self, user_id, quote):
        """Saves a quote for a specific user."""
        with open(self.quotes_file_path, "a") as file:
            file.write(f"{user_id}|{quote}\n")  # Store with user ID as identifier

    def get_user_quotes(self, user_id):
        """Retrieve quotes for a specific user from the file."""
        quotes = []
        with open(self.quotes_file_path, "r") as file:
            for line in file:
                id_, quote = line.strip().split("|", 1)
                if int(id_) == user_id:
                    quotes.append(quote)
        return quotes

    @commands.command(name="filly")
    async def filly(self, ctx):
        """Filly."""
        await ctx.send(self.fetch_random_derpibooru_image("oc:anonfilly, safe"))

    @commands.command(name="derpi")
    async def derpi(self, ctx, *, tags: str):
        """Get a random derpi image with your tags. (seperated by commas)"""
        correct_tags = tags
        if ctx.channel.is_nsfw():
            await ctx.send('Channel is NSFW, "safe" tag not enforced.')
        else:
            correct_tags = "safe, " + tags

        await ctx.send("**Tags: **" + correct_tags)
        if "explicit" in correct_tags:
            await ctx.send("Caution! Explicit image.")
            await ctx.send(self.fetch_random_derpibooru_image(correct_tags, "56027"))
        else:
            await ctx.send(self.fetch_random_derpibooru_image(correct_tags))

    def fetch_random_derpibooru_image(
        self, tags, filter_id=None, sf="random", pp="1"
    ) -> str:
        # Base URL for the Derpibooru API endpoint
        base_url = "https://derpibooru.org/api/v1/json/search/images"

        # Parameters for the search
        params = {
            "q": tags,  # Tags for search query, e.g., "oc:anonfilly, safe"
            "sf": sf,  # Sort field, "random" to get a random image
            "per_page": pp,  # Limit results to 1 image
        }

        if filter_id is not None:
            params["filter_id"] = filter_id

        # Send the request to the API
        response = requests.get(base_url, params=params)

        # Check if the response is successful
        if response.status_code == 200:
            data = response.json()
            # Check if any images were returned
            if data["images"]:
                image = data["images"][0]  # Get the first (and only) image
                image_url = image["representations"]["full"]
                return image_url
            else:
                return "**No images found for the specified tags.**"
        else:
            print("Error:", response.status_code)
            return "**Error occured, check the logs.**"


# Add this cog to the bot
async def setup(bot):
    await bot.add_cog(Fun(bot))
