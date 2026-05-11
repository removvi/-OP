import asyncio
import functools
import time


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
            except Exception as error:
                print(f"[ERROR] Помилка у {func.__name__}: {error}")
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            try:
                print(f"[{level}] Виклик: {func.__name__}")
                result = func(*args, **kwargs)
                print(f"[{level}] Завершено: {func.__name__} за {time.time() - start:.2f}s")
                return result
            except Exception as error:
                print(f"[ERROR] Помилка у {func.__name__}: {error}")
                raise

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator
