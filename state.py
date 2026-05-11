from core.cache import Memoizer
from core.events import build_events
from core.queue import BiDirectionalPriorityQueue


class BotState:
    def __init__(self):
        self.queue = BiDirectionalPriorityQueue()
        self.memo_cache = Memoizer(max_size=100, ttl=600)
        self.events = build_events()
        self.current_track = None
        self.last_guild = None
        self.last_voice_channel = None
        self.volume = 1.0


state = BotState()
