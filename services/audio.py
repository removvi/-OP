import asyncio
import time

import discord
import yt_dlp

from config import FFMPEG_OPTIONS, FFMPEG_PATH, YDL_OPTIONS
from services.spotify import normalize_query
from state import state
from utils.logger import log


async def async_map(func, items):
    return await asyncio.gather(*(func(item) for item in items))


@log("INFO")
async def extract_audio_info(query):
    query = await normalize_query(query)
    cached = state.memo_cache.get(query)
    if cached:
        print("Взято з memoization cache")
        return cached

    def extract():
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(query, download=False)
            if "entries" in info:
                info = info["entries"][0]
            return {
                "audio_url": info["url"],
                "title": info.get("title", "Unknown"),
                "webpage_url": info.get("webpage_url", query),
                "duration": info.get("duration", 0),
            }

    result = await asyncio.to_thread(extract)
    state.memo_cache.set(query, result)
    return result


async def play_next(guild, client):
    if state.queue.is_empty():
        state.current_track = None
        return

    query = state.queue.dequeue(mode="oldest")

    try:
        info = await extract_audio_info(query)
        state.current_track = {
            "title": info["title"],
            "url": info["webpage_url"],
            "duration": info["duration"],
            "start_time": time.time(),
            "paused_total": 0,
            "paused_at": None,
            "status": "playing",
        }

        audio_source = discord.FFmpegPCMAudio(
            info["audio_url"],
            executable=FFMPEG_PATH,
            **FFMPEG_OPTIONS,
        )
        source = discord.PCMVolumeTransformer(audio_source)
        source.volume = state.volume

        voice_client = guild.voice_client
        if voice_client:
            state.events.emit("track_started", info["title"])
            voice_client.play(
                source,
                after=lambda error: asyncio.run_coroutine_threadsafe(
                    play_next(guild, client), client.loop
                ),
            )
    except Exception as error:
        print(f"Помилка відтворення: {error}")
        state.current_track = None
