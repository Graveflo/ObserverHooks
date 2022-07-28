# - * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ ❧
"""
from _weakref import ref
from _weakrefset import WeakSet
from functools import partial
from weakref import WeakMethod
from types import LambdaType

from ram_util.utilities import OrderedSet

from typing import Callable, Iterable, Type

from .common import AbortNotifyException


class EventHandler:
    __slots__ = 'subs', 'owner', '__weakref__',

    def __init__(self):
        self.subs = self.make_weak_collection()

    def make_weak_collection(self):
        return OrderedWeakSet()

    def remove_many(self, funcs: Iterable[Callable]):
        self.subs.difference_update(funcs)

    def update(self, funcs: Iterable[Callable]):
        self.subs.update(funcs)

    def subscribe(self, func: Callable):
        self.subs.add(func)

    def unsubscribe(self, func: Callable):
        self.subs.remove(func)

    def __iadd__(self, other):
        self.subscribe(other)
        return self

    def __isub__(self, other):
        self.unsubscribe(other)
        return self

    def __call__(self, *args, **kwargs):
        for subf in self.subs:
            subf(*args, **kwargs)

    def __len__(self):
        return len(self.subs)

    def __iter__(self):
        return iter(self.subs)

    def purge(self):
        self.subs.clear()

    def duplicate(self) -> 'EventHandler':
        ev = EventHandler()
        ev.subs.update(self.subs)
        return ev

    def emit(self, *args, **kwargs):
        return self.__call__(*args, **kwargs)


class HardRefEventHandler(EventHandler):
    __slots__ = 'hard_links',

    def __init__(self):
        super(HardRefEventHandler, self).__init__()
        self.hard_links = set()

    def hard_subscribe(self, func: Callable):
        self.hard_links.add(func)
        super(HardRefEventHandler, self).subscribe(func)

    def hard_unsubscribe(self, func: Callable):
        super(HardRefEventHandler, self).unsubscribe(func)
        self.hard_links.remove(func)

    def soft_subscribe(self, func: Callable):
        super(HardRefEventHandler, self).subscribe(func)

    def soft_unsubscribe(self, func: Callable):
        super(HardRefEventHandler, self).unsubscribe(func)

    def subscribe(self, func: Callable):
        if isinstance(func, partial):
            self.hard_subscribe(func)
        elif isinstance(func, LambdaType):
            self.hard_subscribe(func)
        else:
            super(HardRefEventHandler, self).subscribe(func)

    def unsubscribe(self, func: Callable):
        if func in self.subs:
            super(HardRefEventHandler, self).unsubscribe(func)
        if func in self.hard_links:
            self.hard_links.remove(func)


class EventFunc(EventHandler):
    __slots__ = 'func', 'auto_fire'

    def __init__(self, func: Callable, auto_fire=True):
        super(EventFunc, self).__init__()
        self.func = func
        self.auto_fire = auto_fire

    @property
    def event_handler(self) -> EventHandler:
        return self

    def __call__(self, *args, **kwargs):
        try:
            ret = self.func(*args, **kwargs)
        except AbortNotifyException as e:
            return e.return_value
        else:
            if self.auto_fire:
                super(EventFunc, self).__call__(*args, **kwargs)
        return ret

    def emit(self, *args, **kwargs):
        super(EventFunc, self).__call__(*args, **kwargs)


class BoundEvent:
    __slots__ = 'event_handler', '__self__', '__func__', 'name', 'origin', '__weakref__'

    def __init__(self, func, obj_ref, event_handler: EventHandler, name, origin):
        self.__self__ = obj_ref
        self.__func__ = func
        self.event_handler = event_handler
        self.name = name
        self.origin = origin

    def __eq__(self, other):
        return self.__func__ is other.__func__

    def __hash__(self):
        return hash(id(self.__func__))

    def make_weak_collection(self):
        return self.event_handler.make_weak_collection()

    def __getattr__(self, item):
        try:
            return super(BoundEvent, self).__getattr__(item)
        except AttributeError:
            pass
        return self.event_handler.__getattribute__(item)

    def __call__(self, *args, **kwargs):
        ret = None
        if not self.origin:
            try:
                ret = self.__func__(self.__self__, *args, **kwargs)
            except AbortNotifyException as e:
                return e.return_value
            self.origin = ret
        self.event_handler(*args, **kwargs)
        self.origin = None
        return ret

    def duplicate(self) -> 'BoundEvent':
        return BoundEvent(self.__func__, self.__self__, self.event_handler.duplicate())

    def switch_event_handler(self, event_handler: EventHandler):
        event_handler.update(self.event_handler)
        event_handler.owner = self.event_handler.owner
        setattr(self.__self__, self.name, event_handler)


class ManualBoundEvent(BoundEvent):  # Must be discrete class for the WeakBoundMethod hack
    def __call__(self, *args, **kwargs):
        try:
            ret = self.__func__(self.__self__, *args, **kwargs)
        except AbortNotifyException as e:
            return e.return_value
        return ret


class BlockSideEffects:
    __slots__ = 'bound_event', 'only'

    def __init__(self, bound_event: BoundEvent | EventFunc, only: Iterable[Callable] | bool = False):
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
            self.only = self.bound_event.event_handler.subs
            self.bound_event.event_handler.subs = self.bound_event.make_weak_collection()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.bound_event.update(self.only)


class EventDescriptor:
    __slots__ = 'true_owner', 'origin', 'event_reg', 'no_origin', 'bound_event_t', 'handler_t'

    def __init__(self, stub: Callable, bound_event_t: Type[BoundEvent], event_name: str = None, no_origin=False,
                 handler_t=EventHandler):
        if event_name is None:
            event_name = '_' + stub.__name__
        self.origin = stub
        self.event_reg = event_name
        self.no_origin = no_origin
        self.bound_event_t = bound_event_t
        self.handler_t = handler_t

    def __set_name__(self, owner, name):
        if not hasattr(self, 'true_owner'):
            self.true_owner = owner
        # for tt in owner.__mro__[1:]:
        #     if name in dir(tt):
        #         object.__getattribute__(tt, name).true_owner = tt

    def __get__(self, instance: object, owner: Type) -> BoundEvent | Callable:
        event_reg = self.event_reg
        try:
            istc = getattr(instance, event_reg)
            if istc.owner is not self.true_owner:  # This is true when this is a super() call
                istc = lambda *x, **y: None
        except AttributeError:
            istc = self.handler_t()
            istc.owner = self.true_owner
            setattr(instance, event_reg, istc)
        return self.bound_event_t(self.origin, instance, istc, event_reg, self.no_origin)


class WeakBoundEvent(WeakMethod):
    __slots__ = ('event_handler', 'name', 'origin')

    def __new__(cls, meth, event_handler, callback=None):
        obj = super(WeakBoundEvent, cls).__new__(cls, meth, callback=callback)
        obj.event_handler = ref(event_handler)
        obj.name = meth.name
        obj.origin = meth.origin
        return obj

    def __init__(self, meth, event_handler, callback=None):
        super(WeakBoundEvent, self).__init__(meth, callback)

    def __call__(self):
        obj = super(WeakMethod, self).__call__()
        func = self._func_ref()
        event_handler = self.event_handler()
        if (obj is None) or (func is None) or (event_handler is None):
            return None
        return self._meth_type(func, obj, event_handler, self.name, self.origin)


class OrderedWeakSet(WeakSet):
    def __init__(self, iterable=None):
        super(OrderedWeakSet, self).__init__()
        self.data = OrderedSet()
        if iterable is not None:
            self.update(iterable)

    def update(self, other: Iterable[callable]) -> None:
        for xi in other:
            self.add(xi)

    def add(self, func: callable) -> None:
        if hasattr(func, '__self__'):
            if self._pending_removals:
                self._commit_removals()
            if isinstance(func, BoundEvent):
                self.data.add(WeakBoundEvent(func, func.event_handler, callback=self._remove))
            else:
                self.data.add(WeakMethod(func, self._remove))
        else:
            super(OrderedWeakSet, self).add(func)

    def remove(self, func: callable) -> None:
        if hasattr(func, '__self__'):
            if self._pending_removals:
                self._commit_removals()
            if isinstance(func, BoundEvent):
                self.data.remove(WeakBoundEvent(func, func.event_handler))
            else:
                self.data.remove(WeakMethod(func))
        else:
            super(OrderedWeakSet, self).remove(func)

    def __contains__(self, func):
        if hasattr(func, '__self__'):
            if self._pending_removals:
                self._commit_removals()
            if type(func) == BoundEvent:
                func = WeakBoundEvent(func, func.event_handler)
            else:
                func = WeakMethod(func)
            return func in self.data
        else:
            return super(OrderedWeakSet, self).__contains__(func)

    def difference_update(self, items: Iterable):
        for item in items:
            if item in self:
                self.remove(item)

