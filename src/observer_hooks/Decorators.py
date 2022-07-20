import inspect
from functools import partial
from typing import Callable

from observer_hooks.ObserverHooks import ManualBoundEvent, EventFunc, BoundEvent, EventDescriptor, EventHandler


def notify_fork(stub: Callable, event_name: str = None, no_origin=False, is_method=None,
              auto_fire=True) -> EventDescriptor | EventHandler:
    if is_method is None:
        args = list(inspect.signature(stub).parameters.keys())
        is_method = args and args[0] == 'self'
    if no_origin:
        if not auto_fire:
            raise ValueError('No-origin function must autofire or calling them wouldnt make sense')
        if is_method:
            bt = BoundEvent if auto_fire else ManualBoundEvent
            return EventDescriptor(stub, bt, event_name=event_name, no_origin=True)
        else:
            return EventHandler()
    else:
        if is_method:
            bt = BoundEvent if auto_fire else ManualBoundEvent
            return EventDescriptor(stub, bt, event_name=event_name)
        else:
            return EventFunc(stub)


def notify(event_name: str = None, no_origin=False, is_method=None, auto_fire=True) -> Callable[[...], BoundEvent | EventFunc]:
    return partial(notify_fork, event_name=event_name, no_origin=no_origin, is_method=is_method, auto_fire=auto_fire)
