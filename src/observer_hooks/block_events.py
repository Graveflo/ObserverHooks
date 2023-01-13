from typing import Iterable, Callable

from observer_hooks import FunctionStub

# - * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ ❧
"""


class FullBlockEventHandlerProxy:
    def __init__(self, event_handler):
        object.__setattr__(self, 'event_handler', event_handler)
        object.__setattr__(self, 'times', 0)

    def __getattr__(self, item):
        try:
            object.__getattribute__(self, item)
        except AttributeError:
            return getattr(self.event_handler, item)

    def __setattr__(self, key, value):
        return setattr(self.event_handler, key, value)

    def __call__(self, *args, **kwargs):
        pass

    def mod_call(self, *args, **kwargs):
        pass


class BlockSideEffects:
    __slots__ = 'bound_event', 'only'

    def __init__(self, bound_event: FunctionStub, only: Iterable[Callable] | bool = False):
        self.bound_event = bound_event
        if only:
            onlyb = bound_event.event_handler.make_weak_collection()
            onlyb.update(only)
            only = onlyb
        self.only = only

    def __enter__(self):
        if self.only:
            self.bound_event.remove_many(self.only)
        else:
            event_handler = self.bound_event.event_handler
            if isinstance(event_handler, FullBlockEventHandlerProxy):
                object.__setattr__(event_handler, 'times', object.__getattribute__(event_handler, 'times') + 1)
            else:
                proxy = FullBlockEventHandlerProxy(self.bound_event.event_handler)
                self.bound_event.switch_event_handler(proxy, update=False)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.only:
            self.bound_event.update(self.only)
        else:
            event_handler = self.bound_event.event_handler
            if isinstance(event_handler, FullBlockEventHandlerProxy):
                times = object.__getattribute__(event_handler, 'times')
                object.__setattr__(event_handler, 'times', times - 1)
                if times <= 1:
                    real_handler = object.__getattribute__(event_handler, 'event_handler')
                    self.bound_event.switch_event_handler(real_handler, update=False)
