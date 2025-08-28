import discord
from discord.ext import commands
from discord import app_commands
from discord import Embed
import asyncio
from colorama import Fore, init
import datetime
import os
init(autoreset=True)

class UnbanView(discord.ui.View):
    def __init__(self, bans_list, timeout=60):
        super().__init__(timeout=timeout)
        self.bans = bans_list
        self.current_page = 0
        self.page_size = 10
        self.pages = [self.bans[i:i + self.page_size] for i in range(0, len(self.bans), self.page_size)]
        self.selected_user = None
    
    def create_embed(self):
        embed = discord.Embed(title="Banned Users List", color=0x2b2d31)
        
        current_page_bans = self.pages[self.current_page]
        for i, user in enumerate(current_page_bans, start=1):
            global_index = (self.current_page * self.page_size) + i
            embed.add_field(
                name=f"{global_index}. {user}",
                value=f"ID: {user.id}",
                inline=False
            )
        
        embed.set_footer(text=f"Page {self.current_page + 1}/{len(self.pages)}")
        return embed
    
    async def update_message(self, interaction):
        embed = self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(emoji="⬅️", style=discord.ButtonStyle.secondary)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            await self.update_message(interaction)
    
    @discord.ui.button(emoji="➡️", style=discord.ButtonStyle.secondary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            await self.update_message(interaction)
    
    @discord.ui.select(
        placeholder="Select a user to unban...",
        min_values=1,
        max_values=1,
        options=[]
    )
    async def user_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        selected_id = select.values[0]
        user = discord.Object(id=int(selected_id))
        
        try:
            await interaction.guild.unban(user)
            embed = discord.Embed(
                title="Successfully Unbanned!",
                description=f"User with ID {selected_id} has been unbanned.",
                color=0x00ff00
            )
            await interaction.response.edit_message(embed=embed, view=None)
        except discord.NotFound:
            embed = discord.Embed(
                title="Error",
                description="User not found in the ban list.",
                color=0xff0000
            )
            await interaction.response.edit_message(embed=embed, view=None)
        except discord.Forbidden:
            embed = discord.Embed(
                title="Permission Denied",
                description="I don't have permission to unban this user.",
                color=0xff0000
            )
            await interaction.response.edit_message(embed=embed, view=None)
        except Exception as e:
            embed = discord.Embed(
                title="Error",
                description=f"Failed to unban: {e}",
                color=0xff0000
            )
            await interaction.response.edit_message(embed=embed, view=None)
    
    async def on_timeout(self):
        pass
    
    def update_select_options(self):
        current_page_bans = self.pages[self.current_page]
        
        options = []
        for user in current_page_bans:
            options.append(discord.SelectOption(
                label=f"{user}",
                description=f"ID: {user.id}",
                value=str(user.id)
            ))
        
        for child in self.children:
            if isinstance(child, discord.ui.Select):
                child.options = options
                break

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ban", description="Ban a user from the server. (Mods only)")
    @app_commands.describe(member="The user to be banned.", reason="The reason for the ban.")
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.guild_only()
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        if member == interaction.user:
            await interaction.response.send_message("You cannot ban yourself.", ephemeral=True)
            return
        if member == self.bot.user:
            await interaction.response.send_message("You cannot ban the bot.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        await member.ban(reason=reason)
        
        if reason:
            await interaction.followup.send(f"{member.mention} was banned for: {reason}.", ephemeral=False)
            print(Fore.RED + f"{interaction.user} banned {member} for: {reason}.")
        else:
            await interaction.followup.send(f"{member.mention} was banned.", ephemeral=False)
            print(Fore.RED + f"{interaction.user} banned {member}.")

    @app_commands.command(name="kick", description="Kick a user from the server. (Mods only)")
    @app_commands.describe(member="The user to be kicked.", reason="The reason for the kick.")
    @app_commands.checks.has_permissions(kick_members=True)
    @app_commands.guild_only()
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        if member == interaction.user:
            await interaction.response.send_message("You cannot kick yourself.", ephemeral=True)
            return
        if member == self.bot.user:
            await interaction.response.send_message("You cannot kick the bot.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        await member.kick(reason=reason)
    
        if reason:
            await interaction.followup.send(f"{member.mention} was kicked for: {reason}.", ephemeral=False)
            print(Fore.RED + f"{interaction.user} kicked {member} for: {reason}.")
        else:
            await interaction.followup.send(f"{member.mention} was kicked.", ephemeral=False)
            print(Fore.RED + f"{interaction.user} kicked {member}.")

    @app_commands.command(name='timeout', description='Timeouts a user for a specific time (Mods only)')
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.guild_only()
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, seconds: int = 0, minutes: int = 0, hours: int = 0, days: int = 0, reason: str = None):
        if member == interaction.user:
            await interaction.response.send_message("You cannot timeout yourself.", ephemeral=True)
            return
        
        if member == self.bot.user:
            await interaction.response.send_message("You cannot timeout the bot.", ephemeral=True)
            return

        duration = datetime.timedelta(seconds=seconds, minutes=minutes, hours= hours, days=days)
        await member.timeout(duration, reason=reason)
        await interaction.response.send_message(f'{member.mention} was timeouted until for {duration}', ephemeral=True)

    @app_commands.command(name="unban", description="Unban a user from the server. (Mods only)")
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.guild_only()
    async def unban(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            bans = []
            async for ban_entry in interaction.guild.bans():
                bans.append(ban_entry.user)
        except discord.Forbidden:
            await interaction.followup.send("Não tenho permissão para ver a lista de bans.")
            return
        except Exception as e:
            await interaction.followup.send(f"Erro ao obter lista de bans: {e}")
            return
        
        if not bans:
            await interaction.followup.send("Não há users banidos.")
            return
        
        view = UnbanView(bans)
        view.update_select_options()
        
        embed = view.create_embed()
        await interaction.followup.send(embed=embed, view=view)

    @app_commands.command(name="untimeout", description="Remove timeout from a user (Mods only)")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.guild_only()
    @app_commands.describe(member="The user to remove timeout from.")
    async def untimeout(self, interaction: discord.Interaction, member: discord.Member):
        if member == interaction.user:
            await interaction.response.send_message("You cannot untimeout yourself.", ephemeral=True)
            return
        
        if member == self.bot.user:
            await interaction.response.send_message("You cannot untimeout the bot.", ephemeral=True)
            return

        await member.timeout(None)
        await interaction.response.send_message(f'{member.mention} timeout removed.', ephemeral=True)


async def setup(bot):
    await bot.add_cog(Moderation(bot))
