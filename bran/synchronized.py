import threading
import logging

logger = logging.getLogger("synchronized")

def synchronized(func, lock = threading.Lock()):
    if hasattr(func, "__call__"):
        if not hasattr(func, "__lock__"):
            func.__lock__ = lock

        def synced_func(*args, **kws):
            with func.__lock__:
                return func(*args, **kws)

        return synced_func

    callables = {}
    for attr in dir(func):
        if hasattr(func, attr):
            _attr = getattr(func, attr)
            if hasattr(_attr, "__call__"):
                callables[attr] = _attr

    for name, callable in callables.items():
        try:
            callable.__lock__ = lock
            setattr(func, name, synchronized(callable, lock))
        except (TypeError, AttributeError) as e:
            logger.warning(f"Unable to add lock to callable {str(callable)}")

    return func