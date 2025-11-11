import discord
from discord.ext import commands
from discord import app_commands
from colorama import Fore, Style, init
from datetime import datetime, timezone
from typing import Optional
import json
from config import EMBED_COLOR, SERVER_OPTIONS
init(autoreset=True)

class ReportView(discord.ui.Modal, title="Report a User"):
    def __init__(self, reported_user: discord.User, get_guild_config: callable):
        super().__init__()
        self.reported_user = reported_user
        self.get_guild_config = get_guild_config

    reason = discord.ui.TextInput(
        label="Reason for Report",
        style=discord.TextStyle.paragraph,
        placeholder="Describe the reason for reporting this user.",
        required=True,
        max_length=500
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        report_channel_id = self.get_guild_config(interaction.guild.id).get("report_channel")
        if report_channel_id is None:
            await interaction.response.send_message(
                "Report channel not set. Please contact an administrator.",
                ephemeral=True
            )
            return

        report_channel = interaction.guild.get_channel(report_channel_id)
        if report_channel is None:
            await interaction.response.send_message(
                "Report channel not found. Please contact an administrator.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="New User Report",
            color=EMBED_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="Reported User", value=self.reported_user.mention, inline=False)
        embed.add_field(name="Reason", value=self.reason.value, inline=False)
        embed.set_footer(
            text=f"Reported by {interaction.user}",
            icon_url=interaction.user.display_avatar.url
        )
        
        await report_channel.send(embed=embed)
        await interaction.response.send_message(
            "Thank you for your report. The moderators will review it shortly.",
            ephemeral=True
        )

class UnbanView(discord.ui.View):
    def __init__(self, bans_list, timeout=60):
        super().__init__(timeout=timeout)
        self.bans = bans_list
        self.current_page = 0
        self.page_size = 10
        self.pages = [self.bans[i:i + self.page_size] for i in range(0, len(self.bans), self.page_size)]
        self.selected_user = None
    
    def create_embed(self):
        embed = discord.Embed(title="Banned Users List", color=EMBED_COLOR)
        
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
                color=EMBED_COLOR
            )
            await interaction.response.edit_message(embed=embed, view=None)
        except discord.NotFound:
            embed = discord.Embed(
                title="Error",
                description="User not found in the ban list.",
                color=EMBED_COLOR
            )
            await interaction.response.edit_message(embed=embed, view=None)
        except discord.Forbidden:
            embed = discord.Embed(
                title="Permission Denied",
                description="I don't have permission to unban this user.",
                color=EMBED_COLOR
            )
            await interaction.response.edit_message(embed=embed, view=None)
        except Exception as e:
            embed = discord.Embed(
                title="Error",
                description=f"Failed to unban: {e}",
                color=EMBED_COLOR
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
        
    def load_config(self):
        try:
            with open(SERVER_OPTIONS, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_config(self, data):
        with open(SERVER_OPTIONS, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def get_guild_config(self, guild_id):
        data = self.load_config()
        return data.get(str(guild_id), {})

    def update_guild_config(self, guild_id, key, value):
        data = self.load_config()
        guild_id = str(guild_id)
        if guild_id not in data:
            data[guild_id] = {"server_name": "Unknown"}
        data[guild_id][key] = value
        self.save_config(data)

    @commands.Cog.listener()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild):
        guild_id = str(after.id)
        data = self.load_config()

        if guild_id in data:
            if data[guild_id].get("server_name") != after.name:
                data[guild_id]["server_name"] = after.name
                self.save_config(data)

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
            await interaction.followup.send("No permission to view bans list.")
            return
        except Exception as e:
            await interaction.followup.send(f"Error fetching bans list: {e}")
            return
        
        if not bans:
            await interaction.followup.send("No banned users found.")
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

    @app_commands.command(name="report", description="Report a user to the moderators.")
    @app_commands.guild_only()
    async def report(self, interaction: discord.Interaction, user: discord.User):
        await interaction.response.send_modal(ReportView(user, self.get_guild_config))

    @commands.command(name="reportchannel")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def reportchannel(self, ctx: commands.Context, action: Optional[str] = None):
        guild_id = str(ctx.guild.id)
        data = self.load_config()

        if action and action.lower() == "clear":
            if guild_id in data and "report_channel" in data[guild_id]:
                del data[guild_id]["report_channel"]
                self.save_config(data)
                await ctx.send("Report channel removed.", delete_after=5)
                print(
                    f"[REPORTCHANNEL]: Report channel removed for server {Fore.MAGENTA}{ctx.guild.name}{Style.RESET_ALL} "
                    f"(ID: {Fore.YELLOW}{ctx.guild.id}{Style.RESET_ALL})"
                )
            else:
                await ctx.send("No report channel has been configured for this server.", delete_after=5)
                print(
                    f"[REPORTCHANNEL]: No report channel configured for server {Fore.MAGENTA}{ctx.guild.name}{Style.RESET_ALL} "
                    f"(ID: {Fore.YELLOW}{ctx.guild.id}{Style.RESET_ALL})"
                )
        else:
            channel = ctx.channel
            self.update_guild_config(guild_id, "report_channel", channel.id)
            self.update_guild_config(guild_id, "server_name", ctx.guild.name)
            await ctx.send(f"Report channel set to {channel.mention}.", delete_after=5)
            print(
                f"[REPORTCHANNEL]: Report channel set to {Fore.BLUE}{channel.name}{Style.RESET_ALL} "
                f"for server {Fore.MAGENTA}{ctx.guild.name}{Style.RESET_ALL} "
                f"(ID: {Fore.YELLOW}{ctx.guild.id}{Style.RESET_ALL})"
            )


async def setup(bot):
    await bot.add_cog(Moderation(bot))
