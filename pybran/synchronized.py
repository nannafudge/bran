"""
Module for classes and methods pertaining to multithreading
"""


import threading
import logging

logger = logging.getLogger("synchronized")


def synchronized(func, lock=threading.Lock()):
    """
    Wraps an object/function in a thread safe wrapper

    :param func: The target to synchronize
    :param lock: The lock to synchronize with

    :return: Synchronized version of :param func:
    """
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

    for name, _callable in callables.items():
        try:
            _callable.__lock__ = lock
            setattr(func, name, synchronized(_callable, lock))
        except (TypeError, AttributeError):
            logger.warning("Unable to add lock to callable %s", str(_callable))

    return func
