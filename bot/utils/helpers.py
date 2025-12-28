import time
import functools
import asyncio
from typing import Callable

_RATE = {}

def rate_limit(calls: int = 30, per_seconds: int = 60):
    def decorator(func: Callable):
        if asyncio.iscoroutinefunction(func):
            async def wrapper(update, context, *args, **kwargs):
                user = update.effective_user
                if not user:
                    return await func(update, context, *args, **kwargs)
                now = time.time()
                arr = _RATE.setdefault(user.id, [])
                # purge old
                arr[:] = [t for t in arr if now - t < per_seconds]
                if len(arr) >= calls:
                    # rate limit hit
                    try:
                        await update.message.reply_text("Rate limit exceeded. Try again later.")
                    except Exception:
                        pass
                    return
                arr.append(now)
                return await func(update, context, *args, **kwargs)
            return wrapper
        else:
            def wrapper(update, context, *args, **kwargs):
                user = update.effective_user
                if not user:
                    return func(update, context, *args, **kwargs)
                now = time.time()
                arr = _RATE.setdefault(user.id, [])
                arr[:] = [t for t in arr if now - t < per_seconds]
                if len(arr) >= calls:
                    try:
                        update.message.reply_text("Rate limit exceeded. Try again later.")
                    except Exception:
                        pass
                    return
                arr.append(now)
                return func(update, context, *args, **kwargs)
            return wrapper
    return decorator
