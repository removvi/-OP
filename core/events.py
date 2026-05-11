class EventEmitter:
    def __init__(self):
        self.listeners = {}

    def subscribe(self, event_name, callback):
        self.listeners.setdefault(event_name, []).append(callback)

    def unsubscribe(self, event_name, callback):
        if event_name in self.listeners and callback in self.listeners[event_name]:
            self.listeners[event_name].remove(callback)

    def emit(self, event_name, data=None):
        for callback in self.listeners.get(event_name, []):
            callback(data)


def on_track_started(data):
    print(f"[EVENT] Почався трек: {data}")


def on_track_added(data):
    print(f"[EVENT] Додано в чергу: {data}")


def build_events():
    events = EventEmitter()
    events.subscribe("track_started", on_track_started)
    events.subscribe("track_added", on_track_added)
    return events
