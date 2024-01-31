import nextcord


class ChannelThreads:
    """
    A model for a channel and its threads.
    """
    channel: nextcord.TextChannel | nextcord.ForumChannel
    threads: list[nextcord.Thread]

    def __init__(self, channel: nextcord.TextChannel, threads: list[nextcord.Thread]):
        self.channel = channel
        self.threads = threads


def get_channel_threads(guild: nextcord.Guild) -> list[ChannelThreads]:
    """
    Gets all the threads in a guild.
    :param guild: The guild to get the threads for.
    :return: A list of ChannelThreads.
    """
    channel_threads = []
    for channel in guild.channels:
        if channel.id == 1184224284902699151:
            # Exclude October DITL due to unknown Discord bug.
            continue
        if not isinstance(channel, nextcord.TextChannel) and not isinstance(channel, nextcord.ForumChannel):
            continue
        threads = []
        for thread in channel.threads:
            threads.append(thread)
        if threads:
            channel_threads.append(ChannelThreads(channel, threads))
    return channel_threads


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
