import time

from state import state


def get_elapsed():
    track = state.current_track
    if not track:
        return 0

    if track.get("status") == "paused":
        return int(track.get("paused_at", time.time()) - track["start_time"] - track["paused_total"])

    return int(time.time() - track["start_time"] - track["paused_total"])
