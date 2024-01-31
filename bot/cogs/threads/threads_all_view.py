import nextcord

from bot.cogs.threads.threads_helpers import ChannelThreads


PER_PAGE = 10


class ThreadsAllView(nextcord.ui.View):
    def __init__(self, channel_threads: list[ChannelThreads]):
        super().__init__()
        self.channel_threads = channel_threads
        self.current_page = 0
        self.pages = self.split_channel_threads_to_pages()
        self.reset_buttons()

    # on timeout
    async def on_timeout(self):
        for child in self.children:
            if isinstance(child, nextcord.ui.Button):
                child.disabled = True
        self.stop()

    @nextcord.ui.button(label='<', style=nextcord.ButtonStyle.blurple)
    async def previous_page(self, _: nextcord.ui.Button, interaction: nextcord.Interaction):
        if self.current_page == 0:
            return
        self.current_page -= 1
        self.reset_buttons()
        await interaction.response.edit_message(embed=self.current_page_embed, view=self)

    @nextcord.ui.button(label='>', style=nextcord.ButtonStyle.blurple)
    async def next_page(self, _: nextcord.ui.Button, interaction: nextcord.Interaction):
        if self.current_page == len(self.pages) - 1:
            return
        self.current_page += 1
        self.reset_buttons()
        await interaction.response.edit_message(embed=self.current_page_embed, view=self)

    @property
    def prev_disabled(self):
        return self.current_page == 0

    @property
    def next_disabled(self):
        return self.current_page == len(self.pages) - 1

    @property
    def current_page_embed(self):
        embed = nextcord.Embed(title='Active Threads',
                               description='Here is a list of all the active threads in this server.\n'
                                           f'Use the buttons to navigate between pages.\n',
                               color=nextcord.Color.dark_blue())
        for channel_thread in self.pages[self.current_page]:
            threads = []
            for thread in channel_thread.threads:
                threads.append(f'- {thread.mention}')
            embed.add_field(name=channel_thread.channel.name, value='\n'.join(threads), inline=False)
        embed.add_field(name='\u200b', value=f'Page {self.current_page + 1}/{len(self.pages)}', inline=False)
        return embed

    def reset_buttons(self):
        self.previous_page.disabled = self.prev_disabled
        self.next_page.disabled = self.next_disabled

    def split_channel_threads_to_pages(self):
        pages = []
        for i in range(0, len(self.channel_threads), PER_PAGE):
            pages.append(self.channel_threads[i:i + PER_PAGE])
        return pages
