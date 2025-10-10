import discord
from discord.ext import commands
import json
from colorama import Fore, Style, init
from config import SERVER_OPTIONS, EMBED_COLOR
from datetime import datetime, timezone
from typing import Optional
import asyncio

init(autoreset=True)

def truncate(text, limit):
    return text if len(text) <= limit else text[:limit-3] + "..."

class ServerLogs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ignored_channels = set()
    
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

    async def send_embed(self, guild, embed):
        if guild.id in self.ignored_channels:
            return
            
        guild_config = self.get_guild_config(guild.id)
        channel_id = guild_config.get("log_channel")
        if not channel_id:
            return
            
        channel = self.bot.get_channel(channel_id)
        if channel:
            self.ignored_channels.add(guild.id)
            try:
                await channel.send(embed=embed)
            except Exception as e:
                print(f"Error sending log: {e}")
            finally:
                await asyncio.sleep(1)
                self.ignored_channels.discard(guild.id)

    # Message Events
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot or not message.guild:
            return

        content = truncate(message.content or "No content", 1024)
        attachments = truncate("\n".join(f"[{a.filename}]({a.url})" for a in message.attachments), 1024) if message.attachments else None
        embeds_text = truncate("\n".join(f"[Embed URL]({e.url})" if e.url else "No embed URL" for e in message.embeds), 1024) if message.embeds else None
        stickers_text = truncate("\n".join(f"[Sticker]({s.url})" if s.url else "No sticker URL" for s in message.stickers), 1024) if message.stickers else None

        embed = discord.Embed(title="Message Deleted", color=discord.Color.red(), timestamp=datetime.now(timezone.utc))
        embed.add_field(name="Channel", value=message.channel.mention, inline=False)
        embed.add_field(name="Author", value=f"{message.author.mention} ({message.author.id})", inline=False)
        embed.add_field(name="Content", value=content, inline=False)
        if attachments: embed.add_field(name="Attachments", value=attachments, inline=False)
        if embeds_text: embed.add_field(name="Embeds", value=embeds_text, inline=False)
        if stickers_text: embed.add_field(name="Stickers", value=stickers_text, inline=False)
        embed.set_thumbnail(url=message.author.display_avatar.url)
        embed.set_footer(text=f"Author ID: {message.author.id} | Message ID: {message.id}")

        await self.send_embed(message.guild, embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or not before.guild or before.content == after.content:
            return

        before_content = truncate(before.content or "No content", 1024)
        after_content = truncate(after.content or "No content", 1024)

        embed = discord.Embed(title="Message Edited", color=discord.Color.blue(), timestamp=datetime.now(timezone.utc))
        embed.add_field(name="Channel", value=before.channel.mention, inline=False)
        embed.add_field(name="Author", value=f"{before.author.mention} ({before.author.id})", inline=False)
        embed.add_field(name="Before", value=before_content, inline=False)
        embed.add_field(name="After", value=after_content, inline=False)
        embed.add_field(name="Message Link", value=f"[Jump to Message]({after.jump_url})", inline=False)
        embed.set_thumbnail(url=before.author.display_avatar.url)
        embed.set_footer(text=f"Author ID: {before.author.id} | Message ID: {before.id}")

        await self.send_embed(before.guild, embed)

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages):
        if not messages or not messages[0].guild:
            return
            
        channels = {}
        for message in messages:
            if message.author.bot:
                continue
            if message.channel.id not in channels:
                channels[message.channel.id] = []
            channels[message.channel.id].append(message)
        
        for channel_id, channel_messages in channels.items():
            channel = self.bot.get_channel(channel_id)
            if not channel:
                continue
                
            content = "\n".join([f"{m.author}: {truncate(m.content, 100)}" for m in channel_messages[:10]])
            if len(channel_messages) > 10:
                content += f"\n...and {len(channel_messages) - 10} more messages"
                
            embed = discord.Embed(title="Bulk Message Delete", color=discord.Color.red(), timestamp=datetime.now(timezone.utc))
            embed.add_field(name="Channel", value=channel.mention, inline=False)
            embed.add_field(name="Messages Deleted", value=str(len(channel_messages)), inline=False)
            embed.add_field(name="Sample", value=content, inline=False)
            embed.set_footer(text=f"Channel ID: {channel_id}")
            
            await self.send_embed(channel.guild, embed)

    # Voice Events
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not member.guild:
            return

        if (before.channel == after.channel and 
            before.self_mute == after.self_mute and 
            before.self_deaf == after.self_deaf and
            before.mute == after.mute and
            before.deaf == after.deaf):
            return

        embed = discord.Embed(color=EMBED_COLOR, timestamp=datetime.now(timezone.utc))
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"User ID: {member.id}")

        if before.channel != after.channel:
            if before.channel is None:
                embed.title = "Joined Voice Channel"
                embed.add_field(name="Member", value=f"{member.mention} ({member.id})", inline=False)
                embed.add_field(name="Channel", value=after.channel.mention, inline=False)

            elif after.channel is None:
                embed.title = "Left Voice Channel"
                embed.add_field(name="Member", value=f"{member.mention} ({member.id})", inline=False)
                embed.add_field(name="Channel", value=before.channel.mention, inline=False)

            else:
                embed.title = "Switched Voice Channels"
                embed.add_field(name="Member", value=f"{member.mention} ({member.id})", inline=False)
                embed.add_field(name="From", value=before.channel.mention, inline=False)
                embed.add_field(name="To", value=after.channel.mention, inline=False)
        else:
            changes = []
            is_mute_change = False
            is_deaf_change = False

            if before.self_mute != after.self_mute:
                changes.append(f"Self Mute: {'✅' if after.self_mute else '❌'}")
            if before.self_deaf != after.self_deaf:
                changes.append(f"Self Deafen: {'✅' if after.self_deaf else '❌'}")
            
            if before.mute != after.mute:
                changes.append(f"Server Mute: {'✅' if after.mute else '❌'}")
                is_mute_change = True
                     
            if before.deaf != after.deaf:
                changes.append(f"Server Deafen: {'✅' if after.deaf else '❌'}")
                is_deaf_change = True

            if changes:
                embed.title = "Voice State Updated"
                embed.add_field(name="Member", value=f"{member.mention} ({member.id})", inline=False)
                embed.add_field(name="Channel", value=after.channel.mention if after.channel else "None", inline=False)
                embed.add_field(name="Changes", value="\n".join(changes), inline=False)
                if is_mute_change:
                    await self.who_applied(member, after.mute, "mute", embed)
                if is_deaf_change:
                    await self.who_applied(member, after.deaf, "deafen", embed)

        if embed.title:
            await self.send_embed(member.guild, embed)

    async def who_applied(self, member, is_active, action_type, embed):
        try:
            async for entry in member.guild.audit_logs(limit=5, action=discord.AuditLogAction.member_update):
                if entry.target.id == member.id:
                    if (action_type == "mute" and hasattr(entry.after, 'mute')) or \
                    (action_type == "deafen" and hasattr(entry.after, 'deaf')):
                        
                        time_diff = (datetime.now(timezone.utc) - entry.created_at).total_seconds()
                        
                        if time_diff < 5:
                            embed.add_field(
                                name=f"Applied by", 
                                value=f"{entry.user.mention} ({entry.user.id})",
                                inline=False
                            )
                            break
        except discord.Forbidden:
            embed.add_field(name="Applied by", value="Unknown (No audit log permission)", inline=False)
        except Exception as e:
            print(f"Error checking audit logs: {e}")
            embed.add_field(name="Applied by", value="Unknown", inline=False)

    # Member Events
    @commands.Cog.listener()
    async def on_member_join(self, member):
        embed = discord.Embed(title="Member Joined", color=discord.Color.green(), timestamp=datetime.now(timezone.utc))
        embed.add_field(name="Member", value=f"{member.mention} ({member.id})", inline=False)
        embed.add_field(name="Account Created", value=discord.utils.format_dt(member.created_at, style="R"), inline=False)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"User ID: {member.id}")

        await self.send_embed(member.guild, embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        async for entry in member.guild.audit_logs(limit=5, action=discord.AuditLogAction.ban):
            if entry.target.id == member.id:
                return
                
        async for entry in member.guild.audit_logs(limit=5, action=discord.AuditLogAction.kick):
            if entry.target.id == member.id:
                embed = discord.Embed(title="Member Kicked", color=discord.Color.orange(), timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Member", value=f"{member} ({member.id})", inline=False)
                embed.add_field(name="Moderator", value=entry.user.mention if entry.user else "Unknown", inline=False)
                embed.add_field(name="Reason", value=entry.reason or "No reason provided", inline=False)
                embed.set_thumbnail(url=member.display_avatar.url)
                embed.set_footer(text=f"User ID: {member.id}")
                await self.send_embed(member.guild, embed)
                return

        embed = discord.Embed(title="Member Left", color=discord.Color.orange(), timestamp=datetime.now(timezone.utc))
        embed.add_field(name="Member", value=f"{member} ({member.id})", inline=False)
        embed.add_field(name="Joined", value=discord.utils.format_dt(member.joined_at, style="R") if member.joined_at else "Unknown", inline=False)
        roles = [r.mention for r in member.roles if r.name != "@everyone"]
        if roles:
            embed.add_field(name="Roles", value=", ".join(roles) if len(roles) < 5 else f"{len(roles)} roles", inline=False)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"User ID: {member.id}")

        await self.send_embed(member.guild, embed)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
            if entry.target.id == user.id:
                embed = discord.Embed(title="Member Banned", color=discord.Color.red(), timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Member", value=f"{user} ({user.id})", inline=False)
                embed.add_field(name="Moderator", value=entry.user.mention if entry.user else "Unknown", inline=False)
                embed.add_field(name="Reason", value=entry.reason or "No reason provided", inline=False)
                embed.set_thumbnail(url=user.display_avatar.url)
                embed.set_footer(text=f"User ID: {user.id}")
                await self.send_embed(guild, embed)
                return

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.unban):
            if entry.target.id == user.id:
                embed = discord.Embed(title="Member Unbanned", color=discord.Color.green(), timestamp=datetime.now(timezone.utc))
                embed.add_field(name="Member", value=f"{user} ({user.id})", inline=False)
                embed.add_field(name="Moderator", value=entry.user.mention if entry.user else "Unknown", inline=False)
                embed.add_field(name="Reason", value=entry.reason or "No reason provided", inline=False)
                embed.set_thumbnail(url=user.display_avatar.url)
                embed.set_footer(text=f"User ID: {user.id}")
                await self.send_embed(guild, embed)
                return

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if not before.guild:
            return
            
        changes = []
        
        if before.nick != after.nick:
            changes.append(f"**Nickname:** {before.nick or 'None'} → {after.nick or 'None'}")
        
        if before.display_avatar.url != after.display_avatar.url:
            changes.append("**Server Avatar:** Updated")
        
        if before.roles != after.roles:
            added = [r.mention for r in after.roles if r not in before.roles]
            removed = [r.mention for r in before.roles if r not in after.roles]
            
            if added:
                changes.append(f"**Roles Added:** {', '.join(added)}")
            if removed:
                changes.append(f"**Roles Removed:** {', '.join(removed)}")
        
        if before.timed_out_until != after.timed_out_until:
            if after.timed_out_until is None:
                changes.append("**Timeout:** Removed")
            else:
                changes.append(f"**Timeout:** Until {discord.utils.format_dt(after.timed_out_until)}")
        
        if changes:
            embed = discord.Embed(title="Member Updated", color=EMBED_COLOR, timestamp=datetime.now(timezone.utc))
            embed.add_field(name="Member", value=f"{after.mention} ({after.id})", inline=False)
            embed.add_field(name="Changes", value="\n".join(changes), inline=False)
            embed.set_thumbnail(url=after.display_avatar.url)
            embed.set_footer(text=f"User ID: {after.id}")
            
            await self.send_embed(after.guild, embed)

    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        changes = []

        if before.name != after.name:
            changes.append(f"**Name:** {before.name} → {after.name}")
            data = self.load_config()
            guild_id = str(after.id)
            
            if guild_id in data:
                data[guild_id]["server_name"] = after.name
                self.save_config(data)

        if before.description != after.description:
            changes.append(f"**Description:** {before.description or 'None'} → {after.description or 'None'}")

        if before.owner != after.owner:
            before_owner = getattr(before.owner, "mention", str(before.owner))
            after_owner = getattr(after.owner, "mention", str(after.owner))
            changes.append(f"**Owner:** {before_owner} → {after_owner}")

        if before.afk_channel != after.afk_channel:
            before_afk = before.afk_channel.mention if before.afk_channel else "None"
            after_afk = after.afk_channel.mention if after.afk_channel else "None"
            changes.append(f"**AFK Channel:** {before_afk} → {after_afk}")

        if before.afk_timeout != after.afk_timeout:
            changes.append(f"**AFK Timeout:** {before.afk_timeout}s → {after.afk_timeout}s")

        if before.icon != after.icon:
            changes.append("**Server Icon:** Updated")

        if before.banner != after.banner:
            changes.append("**Server Banner:** Updated")

        if changes:
            embed = discord.Embed(
                title="Server Updated",
                color=EMBED_COLOR,
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(name="Changes", value="\n".join(changes), inline=False)
            if after.icon:
                embed.set_thumbnail(url=after.icon.url)

            await self.send_embed(after, embed)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        embed = discord.Embed(title="Role Created", color=discord.Color.green(), timestamp=datetime.now(timezone.utc))
        embed.add_field(name="Role", value=role.mention, inline=False)
        embed.add_field(name="Color", value=str(role.color), inline=True)
        embed.add_field(name="Position", value=role.position, inline=True)
        embed.add_field(name="Permissions", value=truncate(", ".join([perm for perm, value in role.permissions if value]), 1024), inline=False)
        embed.set_footer(text=f"Role ID: {role.id}")
        
        await self.send_embed(role.guild, embed)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        embed = discord.Embed(title="Role Deleted", color=discord.Color.red(), timestamp=datetime.now(timezone.utc))
        embed.add_field(name="Role", value=role.name, inline=False)
        embed.add_field(name="Color", value=str(role.color), inline=True)
        embed.add_field(name="Position", value=role.position, inline=True)
        embed.set_footer(text=f"Role ID: {role.id}")
        
        await self.send_embed(role.guild, embed)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        changes = []
        
        if before.name != after.name:
            changes.append(f"**Name:** {before.name} → {after.name}")
        
        if before.color != after.color:
            changes.append(f"**Color:** {before.color} → {after.color}")
        
        if before.hoist != after.hoist:
            changes.append(f"**Hoisted:** {before.hoist} → {after.hoist}")
        
        if before.mentionable != after.mentionable:
            changes.append(f"**Mentionable:** {before.mentionable} → {after.mentionable}")
        
        if before.permissions != after.permissions:
            perms_before = {perm for perm, value in before.permissions if value}
            perms_after = {perm for perm, value in after.permissions if value}
            
            added = perms_after - perms_before
            removed = perms_before - perms_after
            
            if added:
                changes.append(f"**Permissions Added:** {', '.join(added)}")
            if removed:
                changes.append(f"**Permissions Removed:** {', '.join(removed)}")
        
        if changes:
            embed = discord.Embed(title="Role Updated", color=EMBED_COLOR, timestamp=datetime.now(timezone.utc))
            embed.add_field(name="Role", value=after.mention, inline=False)
            embed.add_field(name="Changes", value="\n".join(changes), inline=False)
            embed.set_footer(text=f"Role ID: {after.id}")
            
            await self.send_embed(after.guild, embed)

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild, before, after):
        added = [e for e in after if e not in before]
        removed = [e for e in before if e not in after]
        
        if added or removed:
            embed = discord.Embed(title="Server Emojis Updated", color=EMBED_COLOR, timestamp=datetime.now(timezone.utc))
            
            if added:
                embed.add_field(name="Emojis Added", value="\n".join([f"{e} `:{e.name}:`" for e in added]), inline=False)
            
            if removed:
                embed.add_field(name="Emojis Removed", value="\n".join([f"`:{e.name}:`" for e in removed]), inline=False)
            
            await self.send_embed(guild, embed)

    @commands.Cog.listener()
    async def on_guild_stickers_update(self, guild, before, after):
        added = [s for s in after if s not in before]
        removed = [s for s in before if s not in after]
        
        if added or removed:
            embed = discord.Embed(title="Server Stickers Updated", color=EMBED_COLOR, timestamp=datetime.now(timezone.utc))
            
            if added:
                embed.add_field(name="Stickers Added", value="\n".join([f"{s.name} (`{s.id}`)" for s in added]), inline=False)
            
            if removed:
                embed.add_field(name="Stickers Removed", value="\n".join([f"{s.name} (`{s.id}`)" for s in removed]), inline=False)
            
            await self.send_embed(guild, embed)

    # Channel Events
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        embed = discord.Embed(title="Channel Created", color=discord.Color.green(), timestamp=datetime.now(timezone.utc))
        embed.add_field(name="Channel", value=channel.mention, inline=False)
        embed.add_field(name="Type", value=channel.type.name, inline=True)
        embed.add_field(name="Category", value=channel.category.name if channel.category else "None", inline=True)
        embed.set_footer(text=f"Channel ID: {channel.id}")
        
        await self.send_embed(channel.guild, embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        embed = discord.Embed(title="Channel Deleted", color=discord.Color.red(), timestamp=datetime.now(timezone.utc))
        embed.add_field(name="Channel", value=channel.name, inline=False)
        embed.add_field(name="Type", value=channel.type.name, inline=True)
        embed.add_field(name="Category", value=channel.category.name if channel.category else "None", inline=True)
        embed.set_footer(text=f"Channel ID: {channel.id}")
        
        await self.send_embed(channel.guild, embed)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        changes = []
        
        if before.name != after.name:
            changes.append(f"**Name:** {before.name} → {after.name}")
        
        if before.category != after.category:
            changes.append(f"**Category:** {before.category.name if before.category else 'None'} → {after.category.name if after.category else 'None'}")
        
        if before.position != after.position:
            changes.append(f"**Position:** {before.position} → {after.position}")
        
        if isinstance(before, discord.TextChannel) and isinstance(after, discord.TextChannel):
            if before.topic != after.topic:
                changes.append(f"**Topic:** {before.topic or 'None'} → {after.topic or 'None'}")
            
            if before.is_nsfw() != after.is_nsfw():
                changes.append(f"**NSFW:** {before.is_nsfw()} → {after.is_nsfw()}")
            
            if before.slowmode_delay != after.slowmode_delay:
                changes.append(f"**Slowmode:** {before.slowmode_delay}s → {after.slowmode_delay}s")
        
        if isinstance(before, discord.VoiceChannel) and isinstance(after, discord.VoiceChannel):
            if before.bitrate != after.bitrate:
                changes.append(f"**Bitrate:** {before.bitrate//1000}kbps → {after.bitrate//1000}kbps")
            
            if before.user_limit != after.user_limit:
                changes.append(f"**User Limit:** {before.user_limit} → {after.user_limit}")
        
        if changes:
            embed = discord.Embed(title="Channel Updated", color=EMBED_COLOR, timestamp=datetime.now(timezone.utc))
            embed.add_field(name="Channel", value=after.mention, inline=False)
            embed.add_field(name="Changes", value="\n".join(changes), inline=False)
            embed.set_footer(text=f"Channel ID: {after.id}")
            
            await self.send_embed(after.guild, embed)

    @commands.Cog.listener()
    async def on_guild_channel_pins_update(self, channel, last_pin):
        pins = await channel.pins()
        latest_pin = pins[0] if pins else None
        
        embed = discord.Embed(title="Channel Pins Updated", color=EMBED_COLOR, timestamp=datetime.now(timezone.utc))
        embed.add_field(name="Channel", value=channel.mention, inline=False)
        
        if latest_pin:
            embed.add_field(name="Latest Pin", value=f"[Jump to Message]({latest_pin.jump_url})", inline=False)
            embed.add_field(name="Content", value=truncate(latest_pin.content or "No content", 1024), inline=False)
        
        embed.set_footer(text=f"Channel ID: {channel.id}")
        
        await self.send_embed(channel.guild, embed)

    # Invite Events
    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        embed = discord.Embed(title="Invite Created", color=discord.Color.green(), timestamp=datetime.now(timezone.utc))
        embed.add_field(name="Code", value=invite.code, inline=False)
        embed.add_field(name="Channel", value=invite.channel.mention, inline=True)
        embed.add_field(name="Inviter", value=invite.inviter.mention if invite.inviter else "Unknown", inline=True)
        embed.add_field(name="Max Uses", value=invite.max_uses if invite.max_uses else "Unlimited", inline=True)
        embed.add_field(name="Max Age", value=f"{invite.max_age}s" if invite.max_age else "Never", inline=True)
        embed.add_field(name="Temporary", value=invite.temporary, inline=True)
        embed.set_footer(text=f"Invite Code: {invite.code}")
        
        await self.send_embed(invite.guild, embed)

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        embed = discord.Embed(title="Invite Deleted", color=discord.Color.red(), timestamp=datetime.now(timezone.utc))
        embed.add_field(name="Code", value=invite.code, inline=False)
        embed.add_field(name="Channel", value=invite.channel.mention, inline=True)
        embed.set_footer(text=f"Invite Code: {invite.code}")
        
        await self.send_embed(invite.guild, embed)

    # Thread Events
    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        embed = discord.Embed(title="Thread Created", color=discord.Color.green(), timestamp=datetime.now(timezone.utc))
        embed.add_field(name="Thread", value=thread.mention, inline=False)
        embed.add_field(name="Parent Channel", value=thread.parent.mention, inline=True)
        embed.add_field(name="Owner", value=thread.owner.mention if thread.owner else "Unknown", inline=True)
        embed.set_footer(text=f"Thread ID: {thread.id}")
        
        await self.send_embed(thread.guild, embed)

    @commands.Cog.listener()
    async def on_thread_delete(self, thread):
        embed = discord.Embed(title="Thread Deleted", color=discord.Color.red(), timestamp=datetime.now(timezone.utc))
        embed.add_field(name="Thread", value=thread.name, inline=False)
        embed.add_field(name="Parent Channel", value=thread.parent.mention if thread.parent else "Unknown", inline=True)
        embed.set_footer(text=f"Thread ID: {thread.id}")
        
        await self.send_embed(thread.guild, embed)

    @commands.Cog.listener()
    async def on_thread_update(self, before, after):
        changes = []
        
        if before.name != after.name:
            changes.append(f"**Name:** {before.name} → {after.name}")
        
        if before.archived != after.archived:
            changes.append(f"**Archived:** {before.archived} → {after.archived}")
        
        if before.locked != after.locked:
            changes.append(f"**Locked:** {before.locked} → {after.locked}")
        
        if before.slowmode_delay != after.slowmode_delay:
            changes.append(f"**Slowmode:** {before.slowmode_delay}s → {after.slowmode_delay}s")
        
        if changes:
            embed = discord.Embed(title="Thread Updated", color=EMBED_COLOR, timestamp=datetime.now(timezone.utc))
            embed.add_field(name="Thread", value=after.mention, inline=False)
            embed.add_field(name="Changes", value="\n".join(changes), inline=False)
            embed.set_footer(text=f"Thread ID: {after.id}")
            
            await self.send_embed(after.guild, embed)

    @commands.Cog.listener()
    async def on_thread_member_join(self, member):
        embed = discord.Embed(title="Thread Member Joined", color=discord.Color.green(), timestamp=datetime.now(timezone.utc))
        embed.add_field(name="Member", value=member.mention, inline=False)
        embed.add_field(name="Thread", value=member.thread.mention, inline=False)
        embed.set_footer(text=f"User ID: {member.id} | Thread ID: {member.thread.id}")
        
        await self.send_embed(member.thread.guild, embed)

    @commands.Cog.listener()
    async def on_thread_member_remove(self, member):
        embed = discord.Embed(title="Thread Member Left", color=discord.Color.red(), timestamp=datetime.now(timezone.utc))
        embed.add_field(name="Member", value=member.mention, inline=False)
        embed.add_field(name="Thread", value=member.thread.mention, inline=False)
        embed.set_footer(text=f"User ID: {member.id} | Thread ID: {member.thread.id}")
        
        await self.send_embed(member.thread.guild, embed)

    # Integration Events
    @commands.Cog.listener()
    async def on_integration_create(self, integration):
        embed = discord.Embed(title="Integration Created", color=discord.Color.green(), timestamp=datetime.now(timezone.utc))
        embed.add_field(name="Name", value=integration.name, inline=False)
        embed.add_field(name="Type", value=integration.type, inline=True)
        embed.add_field(name="Enabled", value=integration.enabled, inline=True)
        embed.set_footer(text=f"Integration ID: {integration.id}")
        
        await self.send_embed(integration.guild, embed)

    @commands.Cog.listener()
    async def on_integration_update(self, integration):
        embed = discord.Embed(title="Integration Updated", color=EMBED_COLOR, timestamp=datetime.now(timezone.utc))
        embed.add_field(name="Name", value=integration.name, inline=False)
        embed.add_field(name="Type", value=integration.type, inline=True)
        embed.add_field(name="Enabled", value=integration.enabled, inline=True)
        embed.set_footer(text=f"Integration ID: {integration.id}")
        
        await self.send_embed(integration.guild, embed)

    @commands.Cog.listener()
    async def on_integration_delete(self, integration):
        embed = discord.Embed(title="Integration Deleted", color=discord.Color.red(), timestamp=datetime.now(timezone.utc))
        embed.add_field(name="Name", value=integration.name, inline=False)
        embed.add_field(name="Type", value=integration.type, inline=True)
        embed.set_footer(text=f"Integration ID: {integration.id}")
        
        await self.send_embed(integration.guild, embed)

    # Webhook Events
    @commands.Cog.listener()
    async def on_webhooks_update(self, channel):
        embed = discord.Embed(title="Webhooks Updated", color=EMBED_COLOR, timestamp=datetime.now(timezone.utc))
        embed.add_field(name="Channel", value=channel.mention, inline=False)
        embed.set_footer(text=f"Channel ID: {channel.id}")
        
        await self.send_embed(channel.guild, embed)

    @commands.command(name="logchannel")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def logchannel(self, ctx: commands.Context, action: Optional[str] = None):
        guild_id = str(ctx.guild.id)
        data = self.load_config()

        if action and action.lower() == "clear":
            if guild_id in data and "log_channel" in data[guild_id]:
                del data[guild_id]["log_channel"]
                self.save_config(data)
                await ctx.send("Log channel removed.", delete_after=5)
                print(
                    f"[LOGCHANNEL]: Log channel removed for server {Fore.MAGENTA}{ctx.guild.name}{Style.RESET_ALL} "
                    f"(ID: {Fore.YELLOW}{ctx.guild.id}{Style.RESET_ALL})"
                )
            else:
                await ctx.send("No log channel has been configured for this server.", delete_after=5)
                print(
                    f"[LOGCHANNEL]: No log channel configured for server {Fore.MAGENTA}{ctx.guild.name}{Style.RESET_ALL} "
                    f"(ID: {Fore.YELLOW}{ctx.guild.id}{Style.RESET_ALL})"
                )
        else:
            channel = ctx.channel
            self.update_guild_config(guild_id, "log_channel", channel.id)
            self.update_guild_config(guild_id, "server_name", ctx.guild.name)
            await ctx.send(f"Log channel set to {channel.mention}.", delete_after=5)
            print(
                f"[LOGCHANNEL]: Log channel set to {Fore.BLUE}{channel.name}{Style.RESET_ALL} "
                f"for server {Fore.MAGENTA}{ctx.guild.name}{Style.RESET_ALL} "
                f"(ID: {Fore.YELLOW}{ctx.guild.id}{Style.RESET_ALL})"
            )


async def setup(bot):
    await bot.add_cog(ServerLogs(bot))