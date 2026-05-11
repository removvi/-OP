import time


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
            self.cache.pop(key, None)
            if key in self.usage_order:
                self.usage_order.remove(key)
            return None

        if key in self.usage_order:
            self.usage_order.remove(key)
        self.usage_order.append(key)
        return value

    def set(self, key, value):
        if key in self.cache and key in self.usage_order:
            self.usage_order.remove(key)

        if len(self.cache) >= self.max_size and self.usage_order:
            oldest_key = self.usage_order.pop(0)
            self.cache.pop(oldest_key, None)

        self.cache[key] = (value, time.time())
        self.usage_order.append(key)
