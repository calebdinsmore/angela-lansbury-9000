import nextcord.ui

from bot.cogs.activity import activity_manager
from db.helpers import activity_role_helper


class ActivityStatsView(nextcord.ui.View):
    def __init__(self, stats_embed: nextcord.Embed):
        super().__init__()
        self.stats_embed = stats_embed

    # on timeout
    async def on_timeout(self):
        for child in self.children:
            if isinstance(child, nextcord.ui.Button):
                self.remove_item(child)
        self.stop()

    @nextcord.ui.button(label='Reprocess Roles', style=nextcord.ButtonStyle.secondary)
    async def reprocess_roles(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        if not interaction.guild:
            return
        activity_roles = activity_role_helper.get_activity_roles_for_guild(interaction.guild.id)
        for activity_role in activity_roles:
            activity_role.role = interaction.guild.get_role(activity_role.role_id)
        member = interaction.guild.get_member(interaction.user.id)
        mutations = await activity_manager.process_roles_for_member(member, activity_roles)
        if mutations.errored:
            button.label = '❌ Failed to reprocess roles'
        else:
            button.label = '✅ Roles reprocessed'
        button.disabled = True
        await interaction.response.edit_message(embed=self.stats_embed, view=self)
