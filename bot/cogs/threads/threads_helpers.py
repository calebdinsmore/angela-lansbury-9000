import nextcord


def build_index_embed(guild: nextcord.Guild) -> nextcord.Embed:
    """
    Builds the embed for the threads index message.
    :param guild: The guild to build the embed for.
    :return: The embed.
    """
    embed = nextcord.Embed(title='Active Threads',
                           description='Here is a list of all the active threads in this server.',
                           color=nextcord.Color.dark_blue())
    for channel in guild.channels:
        if not isinstance(channel, nextcord.TextChannel) and not isinstance(channel, nextcord.ForumChannel):
            continue
        threads = []
        for thread in channel.threads:
            threads.append(f'- {thread.mention}')
        if not threads:
            continue
        embed.add_field(name=channel.name, value='\n'.join(threads), inline=False)
    return embed
