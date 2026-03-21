import time


def start_timer(duration):
    if duration is None:
        raise ValueError("duration is required")

    duration = float(duration)
    if duration < 0:
        raise ValueError("duration cannot be negative")

    return time.time()


def get_remaining_time(start_time, duration):
    if start_time is None:
        raise ValueError("start_time is required")
    if duration is None:
        raise ValueError("duration is required")

    elapsed = time.time() - float(start_time)
    remaining = float(duration) - elapsed
    return max(0.0, remaining)


def is_time_over(start_time, duration):
    return get_remaining_time(start_time, duration) <= 0
