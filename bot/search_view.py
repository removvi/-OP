import discord

from bot.helpers import connect_to_voice, safe_defer, safe_send
from services.audio import play_next
from state import state
from utils.time_format import format_time


class SearchSelect(discord.ui.Select):
    def __init__(self, results, client):
        self.client = client
        options = []

        for i, item in enumerate(results):
            title = item.get("title", "Unknown")[:100]
            url = item.get("webpage_url", "")
            duration = item.get("duration")
            description = f"Варіант {i + 1}"
            if duration:
                description += f" • {format_time(duration)}"
            options.append(discord.SelectOption(label=title, description=description, value=url))

        super().__init__(placeholder="Вибери трек", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await safe_defer(interaction)
        state.last_guild = interaction.guild

        voice_client = interaction.guild.voice_client
        if not voice_client:
            voice_client = await connect_to_voice(interaction)
        if not voice_client:
            return

        selected_url = self.values[0]
        state.queue.enqueue(selected_url, priority=10)

        if not voice_client.is_playing() and not voice_client.is_paused():
            await play_next(interaction.guild, self.client)
            if state.current_track:
                await safe_send(
                    interaction,
                    f"Зараз грає: **{state.current_track['title']}** "
                    f"`0:00 / {format_time(state.current_track['duration'])}`",
                )
            else:
                await safe_send(interaction, "Запускаю вибраний трек")
        else:
            await safe_send(interaction, "✅ Додано трек у чергу")


class SearchView(discord.ui.View):
    def __init__(self, results, client):
        super().__init__(timeout=60)
        self.add_item(SearchSelect(results, client))
