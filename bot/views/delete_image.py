import nextcord


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
            await interaction.send("You didn't send the image I'm asking about. Tsk tsk.", ephemeral=True)
            return
        await interaction.send("Okay! I won't touch this one.", ephemeral=True)
        self.stop()

    async def _handle_button(self, days: int, _: nextcord.ui.Button, interaction: nextcord.Interaction):
        original_image = interaction.message.reference
        if interaction.user.id != original_image.cached_message.author.id:
            await interaction.send("You didn't send the image I'm asking about. Tsk tsk.", ephemeral=True)
            return
        await interaction.send(f"You got it! I'll delete your message after {days} day{'s' if days != 1 else ''}.",
                               ephemeral=True)
        self.value = days
        self.stop()
