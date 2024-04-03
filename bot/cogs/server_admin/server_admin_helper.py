import nextcord


def check_perms(guild: nextcord.Guild):
    guild_perms = guild.me.guild_permissions
    results = [
        '## Server-wide Permissions\n> If any of these are disabled, most or all channels will be affected unless they '
        'individually override the server settings.\n',
        'Read Message History: ✅' if guild_perms.read_message_history
        else 'Read Message History: ❌',
        'Manage Messages: ✅' if guild_perms.manage_messages
        else 'Manage Messages: ❌',
        'Send Messages: ✅' if guild_perms.send_messages
        else 'Send Messages: ❌',
        'Manage Threads: ✅' if guild_perms.manage_threads
        else 'Manage Threads: ❌',
        '## Potential Channel Permissions Issues\n> This does not include channels the bot cannot see.\n'
    ]
    return results
