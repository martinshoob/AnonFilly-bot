import discord
from discord.ext import commands


class Fun(commands.Cog, name="Fun"):
    """Fun commands for entertainment."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="edge")
    async def edge(self, ctx, user: discord.Member = None):
        """Edge."""
        await ctx.message.delete()
        # You can replace this with any meme image URL or embed
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


# Add this cog to the bot
async def setup(bot):
    await bot.add_cog(Fun(bot))
