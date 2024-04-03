import nextcord
from nextcord.ext import menus


class CheckPermsPageSource(menus.ListPageSource):
    def __init__(self, data, server_perms_description: str):
        super().__init__(data, per_page=20)
        self.server_perms_description = server_perms_description

    async def format_page(self, menu, entries):
        embed = nextcord.Embed(title='Permissions Check',
                               description=self.server_perms_description,
                               color=nextcord.Color.blurple())
        if not isinstance(entries, list):
            embed.add_field(name=entries[0], value=entries[1], inline=False)
        else:
            for entry in entries:
                embed.add_field(name=entry[0], value=entry[1], inline=False)
        return embed


def get_channel_perm_entries(guild: nextcord.Guild):
    entries = []
    for channel in guild.channels:
        if isinstance(channel, nextcord.VoiceChannel) or isinstance(channel, nextcord.CategoryChannel):
            continue
        channel_issues = []
        perms = channel.permissions_for(guild.me)
        if not perms.view_channel:
            continue
        if not perms.read_message_history:
            channel_issues.append(f'Read Message History: ❌')
        if not perms.manage_messages:
            channel_issues.append(f'Manage Messages: ❌')
        if not perms.send_messages:
            channel_issues.append(f'Send Messages: ❌')
        if not perms.send_messages_in_threads:
            channel_issues.append(f'Send Messages in Threads: ❌')
        if not perms.manage_threads:
            channel_issues.append(f'Manage Threads: ❌')
        if channel_issues:
            entries.append((f'#{channel.name}', '\n'.join(channel_issues)))
    return entries
