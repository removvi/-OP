import asyncio
import time

import discord
from flask import Flask, render_template, request

from services.audio import play_next
from services.progress import get_elapsed
from state import state
from utils.time_format import format_time


def create_web_app(client):
    app = Flask(__name__, template_folder="../templates", static_folder="../static")

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/status")
    def status():
        elapsed = get_elapsed()
        track_data = None

        if state.current_track:
            duration = state.current_track.get("duration", 0)
            track_data = {
                "title": state.current_track["title"],
                "url": state.current_track["url"],
                "duration": duration,
                "duration_text": format_time(duration),
                "elapsed": elapsed,
                "elapsed_text": format_time(elapsed),
                "status": state.current_track.get("status", "playing"),
                "progress": int((elapsed / duration) * 100) if duration else 0,
            }

        return {
            "current": track_data,
            "queue": state.queue.list_queries(),
            "volume": int(state.volume * 100),
        }

    @app.route("/add", methods=["POST"])
    def add_track():
        query = request.form.get("query")
        priority = int(request.form.get("priority", 10))

        if query:
            state.queue.enqueue(query, priority=priority)
            state.events.emit("track_added", query)

            if state.last_guild:
                async def start_from_site():
                    voice_client = state.last_guild.voice_client
                    if not voice_client:
                        if state.last_voice_channel:
                            voice_client = await state.last_voice_channel.connect()
                        else:
                            print("Спочатку зайди у войс і зроби /join")
                            return

                    if not voice_client.is_playing() and not voice_client.is_paused():
                        await play_next(state.last_guild, client)

                asyncio.run_coroutine_threadsafe(start_from_site(), client.loop)

        return {"ok": True}

    @app.route("/skip", methods=["POST"])
    def web_skip():
        if state.last_guild and state.last_guild.voice_client:
            voice_client = state.last_guild.voice_client
            if voice_client.is_playing() or voice_client.is_paused():
                client.loop.call_soon_threadsafe(voice_client.stop)
        return {"ok": True}

    @app.route("/stop", methods=["POST"])
    def web_stop():
        if state.last_guild and state.last_guild.voice_client:
            voice_client = state.last_guild.voice_client
            if voice_client.is_playing():
                if state.current_track:
                    state.current_track["status"] = "paused"
                    state.current_track["paused_at"] = time.time()
                client.loop.call_soon_threadsafe(voice_client.pause)
        return {"ok": True}

    @app.route("/resume", methods=["POST"])
    def web_resume():
        if state.last_guild and state.last_guild.voice_client:
            voice_client = state.last_guild.voice_client
            if voice_client.is_paused():
                if state.current_track:
                    state.current_track["status"] = "playing"
                    state.current_track["paused_total"] += time.time() - state.current_track["paused_at"]
                    state.current_track["paused_at"] = None
                client.loop.call_soon_threadsafe(voice_client.resume)
        return {"ok": True}

    @app.route("/volume", methods=["POST"])
    def web_volume():
        value = request.form.get("volume")
        if value:
            state.volume = max(0, min(int(value) / 100, 2))
            if state.last_guild and state.last_guild.voice_client:
                voice_client = state.last_guild.voice_client
                if voice_client.source and isinstance(voice_client.source, discord.PCMVolumeTransformer):
                    voice_client.source.volume = state.volume
        return {"ok": True}

    @app.route("/leave", methods=["POST"])
    def web_leave():
        state.queue.clear()
        state.current_track = None
        if state.last_guild and state.last_guild.voice_client:
            asyncio.run_coroutine_threadsafe(state.last_guild.voice_client.disconnect(), client.loop)
        return {"ok": True}

    return app
