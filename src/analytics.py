"""
Decorations and logic for instrumenting procedure calls.

Example:

    import analytics

    @analytics.instrumented
    def f(): ...

    f()
    f()

    print(analytics.get())

Note that analytics.instrumented doesn't really make sense for generators.
"""

import collections
import threading
import time

class AnalyticsData(object):
    def __init__(self):
        self.num_calls = 0
        self.num_exceptions = 0
        self.total_time = 0  # in seconds
        self.min_time = None # in seconds
        self.max_time = None # in seconds
    def as_dict(self):
        res = { }
        for attr in ["num_calls", "num_exceptions", "total_time", "min_time", "max_time"]:
            res[attr] = getattr(self, attr)
        return res

_callstack = threading.local()
_lock = threading.RLock()
_data = collections.defaultdict(AnalyticsData)

def safe_min(x, y):
    if x is None:
        return y
    if y is None:
        return x
    return min(x, y)

def safe_max(x, y):
    if x is None:
        return y
    if y is None:
        return x
    return max(x, y)

def instrumented(f):
    def g(*args, **kwargs):
        if not hasattr(_callstack, "value"):
            _callstack.value = []
        _callstack.value.append(f.__name__)
        start = time.time()
        exn_thrown = False
        try:
            return f(*args, **kwargs)
        except:
            exn_thrown = True
            raise
        finally:
            total_time = time.time() - start
            key = "/".join(_callstack.value)
            _callstack.value.pop()
            with _lock:
                entry = _data[key]
                entry.num_calls += 1
                entry.total_time += total_time
                if exn_thrown:
                    entry.num_exceptions += 1
                entry.min_time = safe_min(entry.min_time, total_time)
                entry.max_time = safe_max(entry.max_time, total_time)
    return g

def get():
    res = { }
    with _lock:
        for key, entry in _data.items():
            res[key] = entry.as_dict()
    return res
