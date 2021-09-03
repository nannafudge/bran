"""
Module for classes and methods pertaining to multithreading
"""
import threading
import logging

import inspect

logger = logging.getLogger("synchronized")


def synchronized(func, lock=None):
    """
    Wraps an object/function in a thread safe wrapper

    :param func: The target to synchronize
    :param lock: The lock to synchronize with

    :return: Synchronized version of :param func:
    """

    if lock is None:
        logger.info("Creating new lock for class %s", str(func))
        lock = threading.Lock()

    if inspect.isroutine(func):
        try:
            logger.info("Registering function %s with lock %s", str(func), str(lock))

            setattr(func, "__lock__", lock)

            def synced_func(*args, **kwargs):
                if hasattr(func, "__lock__") and getattr(func, "__lock__").locked():
                    return func(*args, **kwargs)

                with getattr(func, "__lock__"):
                    logger.info("Executing function %s with lock %s", str(func), str(lock))
                    return func(*args, **kwargs)

            setattr(synced_func, "__lock__", lock)

            return synced_func
        except (TypeError, AttributeError, RuntimeError):
            logger.warning("Unable to register function %s with lock %s", str(func), str(lock))

            return func

    methods = inspect.getmembers(func, inspect.isroutine)

    for member in methods:
        try:
            setattr(func, member[0], synchronized(member[1], lock))
        except (TypeError, AttributeError):
            logger.warning("Unable to add lock to function %s", str(member[1]))

    return func
