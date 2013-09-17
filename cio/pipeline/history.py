from collections import defaultdict
from ..utils.thread import ThreadLocalObject


class NodeHistory(ThreadLocalObject):

    def __init__(self):
        super(NodeHistory, self).__init__()
        self._history = defaultdict(list)

    def __len__(self):
        return sum(len(nodes) for nodes in self._history.values())

    def log(self, method, *nodes):
        self._history[method].extend(nodes)

    def list(self, method):
        return self._history[method]

    def clear(self):
        self._history.clear()
