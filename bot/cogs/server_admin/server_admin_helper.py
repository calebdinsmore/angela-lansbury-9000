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
    return results
