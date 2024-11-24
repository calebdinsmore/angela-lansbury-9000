import nextcord

from bot.utils.constants import DO_APRIL_FOOLS
from bot.views.delete_confirmation_view import DeleteConfirmationView


class DeleteImage(nextcord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

    @nextcord.ui.button(label='1d', style=nextcord.ButtonStyle.blurple)
    async def one(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await self._handle_button(1, button, interaction)

    @nextcord.ui.button(label='7d', style=nextcord.ButtonStyle.blurple)
    async def seven(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await self._handle_button(7, button, interaction)

    @nextcord.ui.button(label='14d', style=nextcord.ButtonStyle.blurple)
    async def fourteen(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await self._handle_button(14, button, interaction)

    @nextcord.ui.button(label='30d', style=nextcord.ButtonStyle.blurple)
    async def thirty(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await self._handle_button(30, button, interaction)

    @nextcord.ui.button(label='Keep', style=nextcord.ButtonStyle.gray)
    async def keep(self, _: nextcord.ui.Button, interaction: nextcord.Interaction):
        original_image = interaction.message.reference
        if interaction.user.id != original_image.cached_message.author.id:
            text_content = "You didn't send the image I'm asking about. Tsk tsk."
            if DO_APRIL_FOOLS:
                text_content = "**The Boulder** is confused. " \
                               "You didn't send the image **The Boulder** asked about."
            await interaction.send(text_content, ephemeral=True)
            return
        text_content = "Okay! I won't touch this one."
        if DO_APRIL_FOOLS:
            text_content = "**The Boulder** has processed your request. " \
                           "**The Boulder** will not pulverize your message into dust."
        delete_confirmation_view = DeleteConfirmationView(0, interaction.channel_id, interaction.guild_id,
                                                          interaction.user.id)
        await interaction.send(text_content, ephemeral=True, view=delete_confirmation_view)
        self.stop()

    async def _handle_button(self, days: int, _: nextcord.ui.Button, interaction: nextcord.Interaction):
        original_image = interaction.message.reference
        if interaction.user.id != original_image.cached_message.author.id:
            text_content = "You didn't send the image I'm asking about. Tsk tsk."
            if DO_APRIL_FOOLS:
                text_content = "**The Boulder** is confused. " \
                               "You didn't send the image **The Boulder** asked about."
            await interaction.send(text_content, ephemeral=True)
            return
        text_content = f"You got it! I'll delete your message after {days} day{'s' if days != 1 else ''}."
        if DO_APRIL_FOOLS:
            text_content = "**The Boulder** has processed your request. " \
                           f"**The Boulder** will pulverize your message into dust in {days} day{'s' if days != 1 else ''}."
        delete_confirmation_view = DeleteConfirmationView(days, interaction.channel_id, interaction.guild_id, interaction.user.id)
        await interaction.send(text_content,
                               view=delete_confirmation_view,
                               ephemeral=True)
        self.value = days
        self.stop()
