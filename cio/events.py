from collections import defaultdict


event_listeners = defaultdict(set)


def trigger(name, *args, **kwargs):
    callbacks = event_listeners.get(name)
    if callbacks:
        for callback in callbacks:
            callback(*args, **kwargs)


def listen(name, callback):
    event_listeners[name].add(callback)


def mute(name, callback):
    event_listeners[name].remove(callback)


def clear():
    event_listeners.clear()
