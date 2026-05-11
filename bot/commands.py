import time

import discord
import yt_dlp
from discord import app_commands

from bot.helpers import connect_to_voice, safe_defer, safe_send
from bot.search_view import SearchView
from services.audio import play_next
from services.progress import get_elapsed
from state import state
from utils.logger import log
from utils.time_format import format_time


def register_commands(tree, client):
    @tree.command(name="join", description="Підключити бота до голосового каналу")
    @log("INFO")
    async def join(interaction: discord.Interaction):
        await safe_defer(interaction)
        state.last_guild = interaction.guild
        voice_client = await connect_to_voice(interaction)
        if voice_client:
            await safe_send(interaction, "✅ Я зайшов у голосовий канал")

    @tree.command(name="leave", description="Відключити бота від голосового каналу")
    @log("INFO")
    async def leave(interaction: discord.Interaction):
        await safe_defer(interaction)
        state.last_guild = interaction.guild
        state.current_track = None
        state.queue.clear()

        if interaction.guild.voice_client:
            await interaction.guild.voice_client.disconnect()
            await safe_send(interaction, "Я вийшов з голосового каналу")
        else:
            await safe_send(interaction, "Я не в голосовому каналі")

    @tree.command(name="play", description="Увімкнути музику по назві, YouTube або Spotify-посиланню")
    @app_commands.describe(query="Назва пісні, YouTube-посилання або Spotify-посилання")
    @log("INFO")
    async def play(interaction: discord.Interaction, query: str):
        await safe_defer(interaction)
        state.last_guild = interaction.guild

        voice_client = interaction.guild.voice_client
        if not voice_client:
            voice_client = await connect_to_voice(interaction)
        if not voice_client:
            return

        state.queue.enqueue(query, priority=10)
        state.events.emit("track_added", query)

        if not voice_client.is_playing() and not voice_client.is_paused():
            await play_next(interaction.guild, client)
            if state.current_track:
                await safe_send(
                    interaction,
                    f"Зараз грає: **{state.current_track['title']}** "
                    f"`0:00 / {format_time(state.current_track['duration'])}`",
                )
            else:
                await safe_send(interaction, "Запускаю трек")
        else:
            await safe_send(interaction, f"➕ Додано в чергу: **{query}**")

    @tree.command(name="skip", description="Пропустити поточний трек")
    @log("INFO")
    async def skip(interaction: discord.Interaction):
        await safe_defer(interaction)
        state.last_guild = interaction.guild
        voice_client = interaction.guild.voice_client

        if voice_client and (voice_client.is_playing() or voice_client.is_paused()):
            voice_client.stop()
            await safe_send(interaction, "⏭ Трек пропущено")
        else:
            await safe_send(interaction, "Зараз нічого не грає")

    @tree.command(name="pause", description="Поставити музику на паузу")
    @log("INFO")
    async def pause(interaction: discord.Interaction):
        await safe_defer(interaction)
        voice_client = interaction.guild.voice_client

        if voice_client and voice_client.is_playing():
            if state.current_track:
                state.current_track["status"] = "paused"
                state.current_track["paused_at"] = time.time()
            voice_client.pause()
            await safe_send(interaction, "⏸ Пауза")
        else:
            await safe_send(interaction, "Зараз нічого не грає")

    @tree.command(name="resume", description="Продовжити музику")
    @log("INFO")
    async def resume(interaction: discord.Interaction):
        await safe_defer(interaction)
        state.last_guild = interaction.guild
        voice_client = interaction.guild.voice_client

        if voice_client and voice_client.is_paused():
            if state.current_track:
                state.current_track["status"] = "playing"
                state.current_track["paused_total"] += time.time() - state.current_track["paused_at"]
                state.current_track["paused_at"] = None
            voice_client.resume()
            await safe_send(interaction, "▶️ Продовжено")
        else:
            await safe_send(interaction, "Нема що продовжувати")

    @tree.command(name="queue", description="Показати чергу треків")
    async def queue_command(interaction: discord.Interaction):
        items = state.queue.list_queries()
        if not items:
            await interaction.response.send_message("Черга пуста")
            return

        message = "\n".join([f"{i + 1}. {track}" for i, track in enumerate(items)])
        await interaction.response.send_message(f"Черга:\n{message}")

    @tree.command(name="now", description="Показати що зараз грає")
    async def now(interaction: discord.Interaction):
        if not state.current_track:
            await interaction.response.send_message("Зараз нічого не грає")
            return

        elapsed = get_elapsed()
        duration = state.current_track.get("duration", 0)
        await interaction.response.send_message(
            f"Зараз грає: **{state.current_track['title']}**\n"
            f"⏱ Час: `{format_time(elapsed)} / {format_time(duration)}`"
        )

    @tree.command(name="priorityplay", description="Додати трек у пріоритетну чергу")
    @app_commands.describe(query="Назва або посилання", priority="Менше число = вищий пріоритет")
    async def priorityplay(interaction: discord.Interaction, query: str, priority: int):
        await safe_defer(interaction)
        state.queue.enqueue(query, priority=priority)
        state.events.emit("track_added", query)
        await safe_send(interaction, f"Додано з пріоритетом {priority}: **{query}**")

    @tree.command(name="search", description="Пошук музики з вибором треку")
    @app_commands.describe(query="Назва пісні")
    async def search(interaction: discord.Interaction, query: str):
        await safe_defer(interaction)
        state.last_guild = interaction.guild

        def search_tracks():
            with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
                return ydl.extract_info(f"ytsearch5:{query}", download=False)

        info = await discord.utils.asyncio.to_thread(search_tracks) if False else None
        import asyncio
        info = await asyncio.to_thread(search_tracks)
        results = info.get("entries", [])

        if not results:
            await safe_send(interaction, "Нічого не знайшов")
            return

        await interaction.followup.send("Вибери трек зі списку:", view=SearchView(results, client))
