import nextcord


def check_perms(guild: nextcord.Guild):
    guild_perms = guild.me.guild_permissions
    results = [
        '## Server Permissions\n> If any of these are disabled, most or all channels will be affected unless they '
        'individually override the server settings.\n',
        'Server Read Message History Permission: ✅' if guild_perms.read_message_history
        else 'Server Read Message History Permission: ❌',
        'Server Manage Messages Permission: ✅' if guild_perms.manage_messages
        else 'Server Manage Messages Permission: ❌',
        'Server Send Messages Permission: ✅' if guild_perms.send_messages
        else 'Server Send Messages Permission: ❌',
        '## Potential Channel Permissions Issues\n> This does not include channels the bot cannot see.\n'
    ]
    for channel in guild.channels:
        if isinstance(channel, nextcord.VoiceChannel):
            continue
        channel_perms = channel.permissions_for(guild.me)
        if not channel_perms.view_channel:
            continue
        if not channel_perms.read_message_history:
            results.append(f'{channel.mention} Read Message History Permission: ❌')
        if not channel_perms.manage_messages:
            results.append(f'{channel.mention} Manage Messages Permission: ❌')
        if not channel_perms.send_messages:
            results.append(f'{channel.mention} Send Messages Permission: ❌')
    return results
