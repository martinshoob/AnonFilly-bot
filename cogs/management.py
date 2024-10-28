import discord
from discord.ext import commands


class Management(commands.Cog, name="Management"):
    """Commands for server management."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="purge")
    async def purge(self, ctx, amount: int):
        """Deletes a specified number of messages in the channel."""
        if ctx.author.guild_permissions.manage_messages:
            deleted = await ctx.channel.purge(limit=amount + 1)
            response = await ctx.send(
                f"Deleted {len(deleted) - 1} messages", delete_after=3
            )
            # Delete the invoking command message
            await ctx.message.delete()
        else:
            await ctx.send(
                "You don't have permission to manage messages.", delete_after=3
            )
            await ctx.message.delete()  # Delete the command message

    @commands.command(name="kick")
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        """Kicks a member from the server."""
        if ctx.author.guild_permissions.kick_members:
            await member.kick(reason=reason)
            await ctx.send(f"{member.mention} has been kicked.", delete_after=3)
            await ctx.message.delete()  # Delete the command message
        else:
            await ctx.send("You don't have permission to kick members.", delete_after=3)
            await ctx.message.delete()  # Delete the command message

    @commands.command(name="ban")
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        """Bans a member from the server."""
        if ctx.author.guild_permissions.ban_members:
            await member.ban(reason=reason)
            await ctx.send(f"{member.mention} has been banned.", delete_after=3)
            await ctx.message.delete()  # Delete the command message
        else:
            await ctx.send("You don't have permission to ban members.", delete_after=3)
            await ctx.message.delete()  # Delete the command message

    @commands.command(name="unban")
    async def unban(self, ctx, *, member_name):
        """Unbans a previously banned member."""
        if ctx.author.guild_permissions.ban_members:
            banned_users = await ctx.guild.bans()
            for ban_entry in banned_users:
                user = ban_entry.user
                if user.name == member_name:
                    await ctx.guild.unban(user)
                    await ctx.send(f"{user.mention} has been unbanned.", delete_after=3)
                    await ctx.message.delete()  # Delete the command message
                    return
            await ctx.send(
                f"User '{member_name}' not found in ban list.", delete_after=3
            )
            await ctx.message.delete()  # Delete the command message
        else:
            await ctx.send(
                "You don't have permission to unban members.", delete_after=3
            )
            await ctx.message.delete()  # Delete the command message

    @commands.command(name="mute")
    async def mute(self, ctx, member: discord.Member):
        """Mutes a member by revoking their permission to speak."""
        if ctx.author.guild_permissions.manage_roles:
            mute_role = discord.utils.get(ctx.guild.roles, name="Muted")
            if not mute_role:
                mute_role = await ctx.guild.create_role(name="Muted")
                for channel in ctx.guild.channels:
                    await channel.set_permissions(
                        mute_role, speak=False, send_messages=False
                    )
            await member.add_roles(mute_role)
            await (
                ctx.message.delete()
            )  # Delete the command message before sending response
            await ctx.send(f"{member.mention} has been muted.", delete_after=3)
        else:
            await ctx.send("You don't have permission to mute members.", delete_after=3)
            await ctx.message.delete()  # Delete the command message

    @commands.command(name="unmute")
    async def unmute(self, ctx, member: discord.Member):
        """Unmutes a member by removing the 'Muted' role."""
        if ctx.author.guild_permissions.manage_roles:
            mute_role = discord.utils.get(ctx.guild.roles, name="Muted")
            if mute_role in member.roles:
                await member.remove_roles(mute_role)
                await (
                    ctx.message.delete()
                )  # Delete the command message before sending response
                await ctx.send(f"{member.mention} has been unmuted.", delete_after=3)
            else:
                await ctx.send(f"{member.mention} is not muted.", delete_after=3)
                await ctx.message.delete()  # Delete the command message
        else:
            await ctx.send(
                "You don't have permission to unmute members.", delete_after=3
            )
            await ctx.message.delete()  # Delete the command message

    @commands.command(name="disconnect")
    async def disconnect(self, ctx, member: discord.Member):
        """Disconnects a mentioned user from their current voice channel."""
        await ctx.message.delete()
        # Check if the command issuer has permission to manage roles
        if not ctx.author.guild_permissions.move_members:
            await ctx.send(
                "You don't have permission to disconnect members.", delete_after=3
            )
            return

        # Check if the mentioned member is in a voice channel
        if member.voice is None:
            await ctx.send(
                f"{member.mention} is not connected to a voice channel.", delete_after=3
            )
            return

        # Disconnect the member from the voice channel
        await member.move_to(None)  # Move to None disconnects the user
        await ctx.send(
            f"{member.mention} has been disconnected from their voice channel.",
            delete_after=3,
        )

    @commands.command(name="deafen")
    async def deafen(self, ctx, member: discord.Member):
        """Deafens someone, who is currently in a voice chat."""
        await ctx.message.delete()
        if not ctx.author.guild_permissions.deafen_members:
            await ctx.send(
                "You don't have permission to deafen members.", delete_after=3
            )
            return
        if member.voice is None:
            await ctx.send(
                f"{member.mention} is not connected to a voice channel.", delete_after=3
            )
            return

        await member.edit(deafen=True)
        await ctx.send(f"{member.mention} has been server deafened.", delete_after=3)

    @commands.command(name="undeafen")
    async def undeafen(self, ctx, member: discord.Member):
        """Undeafen someone, who is currently in a voice chat."""
        await ctx.message.delete()
        if not ctx.author.guild_permissions.deafen_members:
            await ctx.send(
                "You don't have permission to undeafen members.", delete_after=3
            )
            return
        if member.voice is None:
            await ctx.send(
                f"{member.mention} is not connected to a voice channel.", delete_after=3
            )
            return

        await member.edit(deafen=False)
        await ctx.send(f"{member.mention} has been unserver deafened.", delete_after=3)


# Add this cog to the bot
async def setup(bot):
    await bot.add_cog(Management(bot))
