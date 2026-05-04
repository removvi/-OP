import discord
from discord import app_commands
import yt_dlp
import asyncio
import threading
import time
import json
import urllib.parse
import urllib.request
import ssl
import heapq
import functools
from dataclasses import dataclass, field
from flask import Flask, render_template, request
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

# ============================================================
# TASK 9: Logging Decorator with Configurable Log Levels
# ============================================================

def log(level="INFO"):
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            try:
                print(f"[{level}] Виклик: {func.__name__}")
                result = await func(*args, **kwargs)
                print(f"[{level}] Завершено: {func.__name__} за {time.time() - start:.2f}s")
                return result
            except Exception as e:
                print(f"[ERROR] Помилка у {func.__name__}: {e}")
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            try:
                print(f"[{level}] Виклик: {func.__name__}")
                result = func(*args, **kwargs)
                print(f"[{level}] Завершено: {func.__name__} за {time.time() - start:.2f}s")
                return result
            except Exception as e:
                print(f"[ERROR] Помилка у {func.__name__}: {e}")
                raise

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


# ============================================================
# TASK 1: Generator Function
# Генератор нескінченно видає ID для треків
# ============================================================

def track_id_generator(start=1):
    current = start
    while True:
        yield current
        current += 1


track_ids = track_id_generator()


# ============================================================
# TASK 1: Iterator with Timeout
# Функція читає iterator певний час
# ============================================================

def consume_iterator_with_timeout(iterator, timeout_seconds):
    start = time.time()
    values = []

    while time.time() - start < timeout_seconds:
        values.append(next(iterator))

    return values


# ============================================================
# TASK 3: Memoization with LRU + TTL
# Кешуємо результати пошуку, щоб не робити повторний yt-dlp запит
# ============================================================

class Memoizer:
    def __init__(self, max_size=50, ttl=300):
        self.cache = {}
        self.usage_order = []
        self.max_size = max_size
        self.ttl = ttl

    def get(self, key):
        if key not in self.cache:
            return None

        value, timestamp = self.cache[key]

        if time.time() - timestamp > self.ttl:
            del self.cache[key]
            return None

        if key in self.usage_order:
            self.usage_order.remove(key)

        self.usage_order.append(key)
        return value

    def set(self, key, value):
        if len(self.cache) >= self.max_size:
            oldest_key = self.usage_order.pop(0)
            self.cache.pop(oldest_key, None)

        self.cache[key] = (value, time.time())
        self.usage_order.append(key)


memo_cache = Memoizer(max_size=100, ttl=600)


# ============================================================
# TASK 4: Bi-Directional Priority Queue
# Черга підтримує priority, oldest, newest, highest, lowest
# ============================================================

@dataclass(order=True)
class QueueItem:
    priority: int
    order: int
    track_id: int = field(compare=False)
    query: str = field(compare=False)


class BiDirectionalPriorityQueue:
    def __init__(self):
        self.items = []
        self.counter = 0

    def enqueue(self, query, priority=10):
        self.counter += 1
        track_id = next(track_ids)
        item = QueueItem(priority, self.counter, track_id, query)
        self.items.append(item)
        return item

    def is_empty(self):
        return len(self.items) == 0

    def clear(self):
        self.items.clear()

    def list_queries(self):
        return [item.query for item in sorted(self.items, key=lambda x: x.order)]

    def dequeue(self, mode="oldest"):
        if not self.items:
            return None

        if mode == "highest":
            selected = min(self.items, key=lambda x: x.priority)
        elif mode == "lowest":
            selected = max(self.items, key=lambda x: x.priority)
        elif mode == "newest":
            selected = max(self.items, key=lambda x: x.order)
        else:
            selected = min(self.items, key=lambda x: x.order)

        self.items.remove(selected)
        return selected.query

    def peek(self, mode="oldest"):
        if not self.items:
            return None

        if mode == "highest":
            return min(self.items, key=lambda x: x.priority)
        elif mode == "lowest":
            return max(self.items, key=lambda x: x.priority)
        elif mode == "newest":
            return max(self.items, key=lambda x: x.order)

        return min(self.items, key=lambda x: x.order)


queue = BiDirectionalPriorityQueue()

# TASK 5: Async Array Function Variant
async def async_map(func, items):
    return await asyncio.gather(*(func(item) for item in items))

# TASK 7: EventEmitter / Reactive Communication
# Внутрішня система подій бота

class EventEmitter:
    def __init__(self):
        self.listeners = {}

    def subscribe(self, event_name, callback):
        self.listeners.setdefault(event_name, []).append(callback)

    def unsubscribe(self, event_name, callback):
        if event_name in self.listeners:
            self.listeners[event_name].remove(callback)

    def emit(self, event_name, data=None):
        for callback in self.listeners.get(event_name, []):
            callback(data)


events = EventEmitter()


def on_track_started(data):
    print(f"[EVENT] Почався трек: {data}")


def on_track_added(data):
    print(f"[EVENT] Додано в чергу: {data}")


events.subscribe("track_started", on_track_started)
events.subscribe("track_added", on_track_added)

# TASK 8: Authentication Proxy
# Проксі для HTTP-запитів з авторизацією
# Використовується для Spotify oEmbed

class AuthProxy:
    def __init__(self, auth_type="none", token=None):
        self.auth_type = auth_type
        self.token = token

    def build_headers(self):
        if self.auth_type == "api_key":
            return {"X-API-Key": self.token}
        if self.auth_type == "jwt":
            return {"Authorization": f"Bearer {self.token}"}
        if self.auth_type == "oauth":
            return {"Authorization": f"OAuth {self.token}"}
        return {}

    def get_json(self, url):
        headers = self.build_headers()
        request_obj = urllib.request.Request(url, headers=headers)
        context = ssl._create_unverified_context()

        with urllib.request.urlopen(request_obj, context=context) as response:
            return json.loads(response.read().decode())


auth_proxy = AuthProxy()

# Discord + Flask

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

current_track = None
last_guild = None
last_voice_channel = None
volume = 1.0

FFMPEG_PATH = r"C:\Users\yeremov\musicBot\ffmpeg.exe"

YDL_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "default_search": "ytsearch",
    "quiet": True
}

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn"
}

app = Flask(__name__)


def format_time(seconds):
    if not seconds:
        return "0:00"

    seconds = int(seconds)
    return f"{seconds // 60}:{seconds % 60:02d}"


def get_elapsed():
    if not current_track:
        return 0

    if current_track.get("status") == "paused":
        return int(
            current_track.get("paused_at", time.time())
            - current_track["start_time"]
            - current_track["paused_total"]
        )

    return int(time.time() - current_track["start_time"] - current_track["paused_total"])


def is_spotify_url(query):
    return "open.spotify.com/track" in query or "open.spotify.com/album" in query


@log("INFO")
def get_spotify_title(spotify_url):
    encoded_url = urllib.parse.quote(spotify_url, safe="")
    oembed_url = f"https://open.spotify.com/oembed?url={encoded_url}"
    data = auth_proxy.get_json(oembed_url)
    return data.get("title", spotify_url)


async def normalize_query(query):
    if is_spotify_url(query):
        try:
            title = await asyncio.to_thread(get_spotify_title, query)
            print(f"Spotify знайдено: {title}")
            return title
        except Exception as e:
            print(f"Помилка Spotify: {e}")
            return "spotify song"

    return query


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/status")
def status():
    elapsed = get_elapsed()

    track_data = None
    if current_track:
        duration = current_track.get("duration", 0)

        track_data = {
            "title": current_track["title"],
            "url": current_track["url"],
            "duration": duration,
            "duration_text": format_time(duration),
            "elapsed": elapsed,
            "elapsed_text": format_time(elapsed),
            "status": current_track.get("status", "playing"),
            "progress": int((elapsed / duration) * 100) if duration else 0
        }

    return {
        "current": track_data,
        "queue": queue.list_queries(),
        "volume": int(volume * 100)
    }


@app.route("/add", methods=["POST"])
def add_track():
    query = request.form.get("query")
    priority = int(request.form.get("priority", 10))

    if query:
        queue.enqueue(query, priority=priority)
        events.emit("track_added", query)

        if last_guild:
            async def start_from_site():
                voice_client = last_guild.voice_client

                if not voice_client:
                    if last_voice_channel:
                        voice_client = await last_voice_channel.connect()
                    else:
                        print("Спочатку зайди у войс і зроби /join")
                        return

                if not voice_client.is_playing() and not voice_client.is_paused():
                    await play_next(last_guild)

            asyncio.run_coroutine_threadsafe(start_from_site(), client.loop)

    return {"ok": True}


@app.route("/skip", methods=["POST"])
def web_skip():
    if last_guild and last_guild.voice_client:
        voice_client = last_guild.voice_client

        if voice_client.is_playing() or voice_client.is_paused():
            client.loop.call_soon_threadsafe(voice_client.stop)

    return {"ok": True}


@app.route("/stop", methods=["POST"])
def web_stop():
    global current_track

    if last_guild and last_guild.voice_client:
        voice_client = last_guild.voice_client

        if voice_client.is_playing():
            if current_track:
                current_track["status"] = "paused"
                current_track["paused_at"] = time.time()

            client.loop.call_soon_threadsafe(voice_client.pause)

    return {"ok": True}


@app.route("/resume", methods=["POST"])
def web_resume():
    global current_track

    if last_guild and last_guild.voice_client:
        voice_client = last_guild.voice_client

        if voice_client.is_paused():
            if current_track:
                current_track["status"] = "playing"
                current_track["paused_total"] += time.time() - current_track["paused_at"]
                current_track["paused_at"] = None

            client.loop.call_soon_threadsafe(voice_client.resume)

    return {"ok": True}


@app.route("/volume", methods=["POST"])
def web_volume():
    global volume

    value = request.form.get("volume")

    if value:
        volume = int(value) / 100
        volume = max(0, min(volume, 2))

        if last_guild and last_guild.voice_client:
            voice_client = last_guild.voice_client

            if voice_client.source and isinstance(voice_client.source, discord.PCMVolumeTransformer):
                voice_client.source.volume = volume

    return {"ok": True}


@app.route("/leave", methods=["POST"])
def web_leave():
    global current_track

    queue.clear()
    current_track = None

    if last_guild and last_guild.voice_client:
        asyncio.run_coroutine_threadsafe(
            last_guild.voice_client.disconnect(),
            client.loop
        )

    return {"ok": True}


def run_web():
    app.run(host="127.0.0.1", port=5000, debug=False)


@client.event
async def on_ready():
    await tree.sync()
    print(f"Bot connected as {client.user}")
    print("Slash commands synced")
    print("Web site: http://127.0.0.1:5000")


async def safe_defer(interaction):
    try:
        if not interaction.response.is_done():
            await interaction.response.defer()
    except discord.NotFound:
        print("Interaction already expired")


async def safe_send(interaction, message):
    try:
        if interaction.response.is_done():
            await interaction.followup.send(message)
        else:
            await interaction.response.send_message(message)
    except discord.NotFound:
        print("Cannot send response: interaction expired")


async def connect_to_voice(interaction: discord.Interaction):
    global last_voice_channel

    if not interaction.user.voice:
        await safe_send(interaction, "Ти не в голосовому каналі")
        return None

    channel = interaction.user.voice.channel
    last_voice_channel = channel

    voice_client = interaction.guild.voice_client

    if voice_client:
        await voice_client.move_to(channel)
    else:
        voice_client = await channel.connect()

    return voice_client


@log("INFO")
async def extract_audio_info(query):
    query = await normalize_query(query)

    cached = memo_cache.get(query)
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
                "duration": info.get("duration", 0)
            }

    result = await asyncio.to_thread(extract)
    memo_cache.set(query, result)
    return result


@log("INFO")
async def play_next(guild):
    global current_track

    if queue.is_empty():
        current_track = None
        return

    query = queue.dequeue(mode="oldest")

    try:
        info = await extract_audio_info(query)

        current_track = {
            "title": info["title"],
            "url": info["webpage_url"],
            "duration": info["duration"],
            "start_time": time.time(),
            "paused_total": 0,
            "paused_at": None,
            "status": "playing"
        }

 # TASK 6: Stream Processing

        audio_source = discord.FFmpegPCMAudio(
            info["audio_url"],
            executable=FFMPEG_PATH,
            **FFMPEG_OPTIONS
        )

        source = discord.PCMVolumeTransformer(audio_source)
        source.volume = volume

        voice_client = guild.voice_client

        if voice_client:
            events.emit("track_started", info["title"])

            voice_client.play(
                source,
                after=lambda e: asyncio.run_coroutine_threadsafe(
                    play_next(guild),
                    client.loop
                )
            )

    except Exception as e:
        print(f"Помилка відтворення: {e}")
        current_track = None


@tree.command(name="join", description="Підключити бота до голосового каналу")
@log("INFO")
async def join(interaction: discord.Interaction):
    global last_guild

    await safe_defer(interaction)

    last_guild = interaction.guild

    voice_client = await connect_to_voice(interaction)

    if voice_client:
        await safe_send(interaction, "✅ Я зайшов у голосовий канал")


@tree.command(name="leave", description="Відключити бота від голосового каналу")
@log("INFO")
async def leave(interaction: discord.Interaction):
    global last_guild, current_track

    await safe_defer(interaction)

    last_guild = interaction.guild
    current_track = None
    queue.clear()

    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        await safe_send(interaction, "👋 Я вийшов з голосового каналу")
    else:
        await safe_send(interaction, "Я не в голосовому каналі")


@tree.command(name="play", description="Увімкнути музику по назві, YouTube або Spotify-посиланню")
@app_commands.describe(query="Назва пісні, YouTube-посилання або Spotify-посилання")
@log("INFO")
async def play(interaction: discord.Interaction, query: str):
    global last_guild

    await safe_defer(interaction)

    last_guild = interaction.guild

    voice_client = interaction.guild.voice_client

    if not voice_client:
        voice_client = await connect_to_voice(interaction)

    if not voice_client:
        return

    queue.enqueue(query, priority=10)
    events.emit("track_added", query)

    if not voice_client.is_playing() and not voice_client.is_paused():
        await play_next(interaction.guild)

        if current_track:
            await safe_send(
                interaction,
                f"🎵 Зараз грає: **{current_track['title']}** "
                f"`0:00 / {format_time(current_track['duration'])}`"
            )
        else:
            await safe_send(interaction, "🎵 Запускаю трек")
    else:
        await safe_send(interaction, f"➕ Додано в чергу: **{query}**")


@tree.command(name="skip", description="Пропустити поточний трек")
@log("INFO")
async def skip(interaction: discord.Interaction):
    global last_guild

    await safe_defer(interaction)

    last_guild = interaction.guild

    voice_client = interaction.guild.voice_client

    if voice_client and (voice_client.is_playing() or voice_client.is_paused()):
        voice_client.stop()
        await safe_send(interaction, "⏭ Трек пропущено")
    else:
        await safe_send(interaction, "Зараз нічого не грає")


@tree.command(name="pause", description="Поставити музику на паузу")
@log("INFO")
async def pause(interaction: discord.Interaction):
    global current_track

    await safe_defer(interaction)

    voice_client = interaction.guild.voice_client

    if voice_client and voice_client.is_playing():
        if current_track:
            current_track["status"] = "paused"
            current_track["paused_at"] = time.time()

        voice_client.pause()
        await safe_send(interaction, "⏸ Пауза")
    else:
        await safe_send(interaction, "Зараз нічого не грає")


@tree.command(name="resume", description="Продовжити музику")
@log("INFO")
async def resume(interaction: discord.Interaction):
    global last_guild, current_track

    await safe_defer(interaction)

    last_guild = interaction.guild

    voice_client = interaction.guild.voice_client

    if voice_client and voice_client.is_paused():
        if current_track:
            current_track["status"] = "playing"
            current_track["paused_total"] += time.time() - current_track["paused_at"]
            current_track["paused_at"] = None

        voice_client.resume()
        await safe_send(interaction, "▶️ Продовжено")
    else:
        await safe_send(interaction, "Нема що продовжувати")


@tree.command(name="queue", description="Показати чергу треків")
async def queue_command(interaction: discord.Interaction):
    items = queue.list_queries()

    if len(items) == 0:
        await interaction.response.send_message("Черга пуста")
    else:
        msg = "\n".join([f"{i + 1}. {track}" for i, track in enumerate(items)])
        await interaction.response.send_message(f"📜 Черга:\n{msg}")


@tree.command(name="now", description="Показати що зараз грає")
async def now(interaction: discord.Interaction):
    if not current_track:
        await interaction.response.send_message("Зараз нічого не грає")
        return

    elapsed = get_elapsed()
    duration = current_track.get("duration", 0)

    await interaction.response.send_message(
        f"🎵 Зараз грає: **{current_track['title']}**\n"
        f"⏱ Час: `{format_time(elapsed)} / {format_time(duration)}`"
    )


@tree.command(name="priorityplay", description="Додати трек у пріоритетну чергу")
@app_commands.describe(query="Назва або посилання", priority="Менше число = вищий пріоритет")
async def priorityplay(interaction: discord.Interaction, query: str, priority: int):
    await safe_defer(interaction)

    queue.enqueue(query, priority=priority)
    events.emit("track_added", query)

    await safe_send(interaction, f"🔥 Додано з пріоритетом {priority}: **{query}**")


class SearchSelect(discord.ui.Select):
    def __init__(self, results):
        options = []

        for i, item in enumerate(results):
            title = item.get("title", "Unknown")[:100]
            url = item.get("webpage_url", "")

            duration = item.get("duration")
            description = f"Варіант {i + 1}"

            if duration:
                description += f" • {format_time(duration)}"

            options.append(
                discord.SelectOption(
                    label=title,
                    description=description,
                    value=url
                )
            )

        super().__init__(
            placeholder="Вибери трек",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        global last_guild

        await safe_defer(interaction)

        last_guild = interaction.guild

        voice_client = interaction.guild.voice_client

        if not voice_client:
            voice_client = await connect_to_voice(interaction)

        if not voice_client:
            return

        selected_url = self.values[0]
        queue.enqueue(selected_url, priority=10)

        if not voice_client.is_playing() and not voice_client.is_paused():
            await play_next(interaction.guild)

            if current_track:
                await safe_send(
                    interaction,
                    f"🎵 Зараз грає: **{current_track['title']}** "
                    f"`0:00 / {format_time(current_track['duration'])}`"
                )
            else:
                await safe_send(interaction, "🎵 Запускаю вибраний трек")
        else:
            await safe_send(interaction, "✅ Додано трек у чергу")


class SearchView(discord.ui.View):
    def __init__(self, results):
        super().__init__(timeout=60)
        self.add_item(SearchSelect(results))


@tree.command(name="search", description="Пошук музики з вибором треку")
@app_commands.describe(query="Назва пісні")
async def search(interaction: discord.Interaction, query: str):
    global last_guild

    await safe_defer(interaction)

    last_guild = interaction.guild

    def search_tracks():
        with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
            return ydl.extract_info(f"ytsearch5:{query}", download=False)

    info = await asyncio.to_thread(search_tracks)

    results = info.get("entries", [])

    if not results:
        await safe_send(interaction, "Нічого не знайшов")
        return

    view = SearchView(results)

    await interaction.followup.send("🎧 Вибери трек зі списку:", view=view)


threading.Thread(target=run_web, daemon=True).start()
client.run(TOKEN)