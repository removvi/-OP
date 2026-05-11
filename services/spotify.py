import asyncio
import urllib.parse

from core.auth_proxy import AuthProxy
from utils.logger import log

_auth_proxy = AuthProxy()


def is_spotify_url(query):
    return "open.spotify.com/track" in query or "open.spotify.com/album" in query


@log("INFO")
def get_spotify_title(spotify_url):
    encoded_url = urllib.parse.quote(spotify_url, safe="")
    oembed_url = f"https://open.spotify.com/oembed?url={encoded_url}"
    data = _auth_proxy.get_json(oembed_url)
    return data.get("title", spotify_url)


async def normalize_query(query):
    if not is_spotify_url(query):
        return query

    try:
        title = await asyncio.to_thread(get_spotify_title, query)
        print(f"Spotify знайдено: {title}")
        return title
    except Exception as error:
        print(f"Помилка Spotify: {error}")
        return "spotify song"
