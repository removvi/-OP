from dataclasses import dataclass, field


def track_id_generator(start=1):
    current = start
    while True:
        yield current
        current += 1


def consume_iterator_with_timeout(iterator, timeout_seconds):
    import time

    start = time.time()
    values = []
    while time.time() - start < timeout_seconds:
        values.append(next(iterator))
    return values


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
        self.track_ids = track_id_generator()

    def enqueue(self, query, priority=10):
        self.counter += 1
        item = QueueItem(priority, self.counter, next(self.track_ids), query)
        self.items.append(item)
        return item

    def is_empty(self):
        return len(self.items) == 0

    def clear(self):
        self.items.clear()

    def list_queries(self):
        return [item.query for item in sorted(self.items, key=lambda item: item.order)]

    def dequeue(self, mode="oldest"):
        item = self.peek(mode)
        if item is None:
            return None
        self.items.remove(item)
        return item.query

    def peek(self, mode="oldest"):
        if not self.items:
            return None
        if mode == "highest":
            return min(self.items, key=lambda item: item.priority)
        if mode == "lowest":
            return max(self.items, key=lambda item: item.priority)
        if mode == "newest":
            return max(self.items, key=lambda item: item.order)
        return min(self.items, key=lambda item: item.order)
