import inspect
from functools import partial
from typing import Callable

from observer_hooks.ObserverHooks import BoundEvent, EventDescriptor, EventHandler, FunctionStub, SuperCopyDescriptor


def notify_fork(stub: Callable, event_name: str = None, no_origin=False, is_method=None,
                auto_fire=True, handler_t=EventHandler, pass_ref=False) -> EventDescriptor | FunctionStub:
    if is_method is None:
        args = list(inspect.signature(stub).parameters.keys())
        is_method = args and args[0] == 'self'
    if is_method:
        pass_ref = 0 if pass_ref else 1
        return EventDescriptor(stub, BoundEvent, event_name=event_name, no_origin=no_origin, handler_t=handler_t,
                               auto=auto_fire, pass_ref=pass_ref)
    else:
        handler = handler_t()
        handler.pass_ref = 0
        return FunctionStub(stub, handler, not no_origin, auto_fire)


def notify(event_name: str = None, no_origin=False, is_method=None, auto_fire=True, handler_t=EventHandler,
           pass_ref=False) -> Callable[[...], BoundEvent | FunctionStub]:
    return partial(notify_fork, event_name=event_name, no_origin=no_origin, is_method=is_method, auto_fire=auto_fire,
                   handler_t=handler_t, pass_ref=pass_ref)


def notify_copy_super(event_name: str = None, no_origin=None, auto_fire=None, handler_t=None, pass_ref=None):
    if pass_ref is not None:
        pass_ref = 0 if pass_ref else 1

    def _(stub):
        return SuperCopyDescriptor(stub, event_name=event_name, no_origin=no_origin, handler_t=handler_t,
                                   auto=auto_fire, pass_ref=pass_ref)
    return _
