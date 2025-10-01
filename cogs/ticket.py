import discord
from discord.ext import commands
import json
import os
import asyncio
from config import SERVER_OPTIONS 

def load_config():
    if not os.path.exists(SERVER_OPTIONS):
        return {}
    with open(SERVER_OPTIONS, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(data):
    with open(SERVER_OPTIONS, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

class TicketPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Open Ticket", style=discord.ButtonStyle.primary, custom_id="ticket_panel:create")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user

        for channel in guild.channels:
            if channel.name.startswith(f"ticket-{user.name}") or channel.name.startswith(f"ticket-{user.display_name}"):
                await interaction.response.send_message(f"You already have an open ticket: {channel.mention}", ephemeral=True)
                return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
        }

        channel = await guild.create_text_channel(f"ticket-{user.name}", overwrites=overwrites)

        data = load_config()
        guild_id = str(guild.id)
        if "open_tickets" not in data[guild_id]:
            data[guild_id]["open_tickets"] = []
        data[guild_id]["open_tickets"].append(channel.id)
        save_config(data)
        
        close_view = CloseTicketView()
        embed = discord.Embed(
            title="Support Ticket",
            description=f"Hello {user.mention}! Support will be with you shortly.\n\nClick the button below to close this ticket.",
            color=discord.Color.green()
        )
        await channel.send(embed=embed, view=close_view)
        
        await self.log_ticket_action(guild, f"Ticket created by {user.mention} ({user.id}) - {channel.mention}")
        
        await interaction.response.send_message(f"Your ticket has been created: {channel.mention}", ephemeral=True)

    async def log_ticket_action(self, guild, message):
        data = load_config()
        guild_id = str(guild.id)
        
        if guild_id in data and "log_channel" in data[guild_id]:
            log_channel_id = data[guild_id]["log_channel"]
            log_channel = guild.get_channel(log_channel_id)
            if log_channel:
                embed = discord.Embed(
                    description=message,
                    color=discord.Color.blue(),
                    timestamp=discord.utils.utcnow()
                )
                await log_channel.send(embed=embed)

class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket:simple")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.channel.name.startswith("ticket-"):
            await interaction.response.send_message("This is not a ticket channel.", ephemeral=True)
            return

        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)
        
        embed = discord.Embed(
            title="Ticket Closed",
            description="This ticket has been closed and will be deleted in 10 seconds.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)
        
        await self.log_ticket_action(interaction.guild, f"Ticket closed by {interaction.user.mention} ({interaction.user.id}) - {interaction.channel.mention}")
        
        data = load_config()
        guild_id = str(interaction.guild.id)
        if "open_tickets" in data[guild_id] and interaction.channel.id in data[guild_id]["open_tickets"]:
            data[guild_id]["open_tickets"].remove(interaction.channel.id)
            save_config(data)

        await asyncio.sleep(10)
        await interaction.channel.delete()

    @discord.ui.button(label="Close with Reason", style=discord.ButtonStyle.secondary, custom_id="close_ticket:reason")
    async def close_with_reason(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.channel.name.startswith("ticket-"):
            await interaction.response.send_message("This is not a ticket channel.", ephemeral=True)
            return

        modal = CloseReasonModal()
        await interaction.response.send_modal(modal)

    async def log_ticket_action(self, guild, message):
        data = load_config()
        guild_id = str(guild.id)
        
        if guild_id in data and "log_channel" in data[guild_id]:
            log_channel_id = data[guild_id]["log_channel"]
            log_channel = guild.get_channel(log_channel_id)
            if log_channel:
                embed = discord.Embed(
                    description=message,
                    color=discord.Color.orange(),
                    timestamp=discord.utils.utcnow()
                )
                await log_channel.send(embed=embed)

class CloseReasonModal(discord.ui.Modal, title="Close Ticket"):
    reason = discord.ui.TextInput(
        label="Reason for closing",
        placeholder="Enter the reason for closing this ticket...",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=500
    )

    async def on_submit(self, interaction: discord.Interaction):
        original_message = None
        async for message in interaction.channel.history(limit=10):
            if message.components:
                original_message = message
                break
        
        if original_message:
            view = discord.ui.View()
            for component in original_message.components[0].children:
                component.disabled = True
            await original_message.edit(view=view)
        
        embed = discord.Embed(
            title="Ticket Closed",
            description=f"**Reason:** {self.reason.value}\n\nThis ticket will be deleted in 10 seconds.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)
        
        await self.log_ticket_action(interaction.guild, f"Ticket closed by {interaction.user.mention} ({interaction.user.id}) - {interaction.channel.mention}\n**Reason:** {self.reason.value}")
        
        data = load_config()
        guild_id = str(interaction.guild.id)
        if "open_tickets" in data.get(guild_id, {}):
            if interaction.channel.id in data[guild_id]["open_tickets"]:
                data[guild_id]["open_tickets"].remove(interaction.channel.id)
                save_config(data)

        await asyncio.sleep(10)
        await interaction.channel.delete()

    async def log_ticket_action(self, guild, message):
        data = load_config()
        guild_id = str(guild.id)
        
        if guild_id in data and "log_channel" in data[guild_id]:
            log_channel_id = data[guild_id]["log_channel"]
            log_channel = guild.get_channel(log_channel_id)
            if log_channel:
                embed = discord.Embed(
                    description=message,
                    color=discord.Color.red(),
                    timestamp=discord.utils.utcnow()
                )
                await log_channel.send(embed=embed)

class Ticket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ticket")
    @commands.has_permissions(administrator=True)
    async def ticket_setup(self, ctx):
        data = load_config()
        guild_id = str(ctx.guild.id)

        if guild_id not in data:
            data[guild_id] = {"server_name": ctx.guild.name}

        data[guild_id]["ticket_panel"] = ctx.channel.id
        save_config(data)

        await ctx.channel.purge(limit=100)

        embed = discord.Embed(
            title="Ticket System",
            description="Click the button below to open a ticket.",
            color=discord.Color.blue()
        )
        await ctx.channel.send(embed=embed, view=TicketPanel())

        await ctx.send("Ticket panel has been set up in this channel.", delete_after=5)

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.wait_until_ready()
        data = load_config()
        for guild_id, cfg in data.items():
            guild = self.bot.get_guild(int(guild_id))
            if not guild:
                continue

            channel_id = cfg.get("ticket_panel")
            if channel_id:
                channel = guild.get_channel(channel_id)
                if channel:
                    await channel.purge(limit=100)
                    embed = discord.Embed(
                        title="Ticket System",
                        description="Click the button below to open a ticket.",
                        color=discord.Color.blue()
                    )
                    await channel.send(embed=embed, view=TicketPanel())

            open_tickets = cfg.get("open_tickets", [])
            for ticket_id in open_tickets:
                ticket_channel = guild.get_channel(ticket_id)
                if ticket_channel:
                    try:
                        async for msg in ticket_channel.history(limit=50):
                            if msg.author == self.bot.user and msg.embeds:
                                await msg.edit(view=CloseTicketView())
                                break
                    except Exception as e:
                        print(f"[TICKET] Error restoring ticket {ticket_id}: {e}")


async def setup(bot):
    await bot.add_cog(Ticket(bot))