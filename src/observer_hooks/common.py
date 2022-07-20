from typing import Iterable

try:
    from ram_util.utilities import OrderedSet
except ImportError:
    class OrderedSet(dict):
        __slots__ = tuple()

        def add(self, value):
            self[value] = None

        def discard(self, item):
            if item in self:
                self.pop(item)

        def remove(self, item):
            self.pop(item)

        def difference_update(self, items: Iterable):
            for item in items:
                if item in self:
                    self.pop(item)


class AbortNotifyException(Exception):
    def __init__(self, return_value, *args, **kwargs):
        self.return_value = return_value
        super(AbortNotifyException, self).__init__(*args, **kwargs)
