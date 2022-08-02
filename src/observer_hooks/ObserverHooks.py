# - * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ ❧
"""
from _weakrefset import WeakSet
from functools import partial
from weakref import WeakMethod
from types import LambdaType

from typing import Callable, Iterable, Type

from .common import AbortNotifyException, OrderedSet


class EventHandler:
    __slots__ = 'subs', 'owner', 'pass_ref', '__weakref__',

    def __init__(self, pass_self=False):
        self.subs = self.make_weak_collection()
        self.pass_ref = 0 if pass_self else 1

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

    def mod_call(self, *args, **kwargs):
        for subf in self.subs:
            subf(*args[self.pass_ref:], **kwargs)

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

    def __init__(self, **kwargs):
        super(HardRefEventHandler, self).__init__(**kwargs)
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


class FunctionStub:
    __slots__ = 'event_handler', '__func__', 'origin', 'auto', '__weakref__'

    def __init__(self, func: Callable, event_handler: EventHandler, origin: bool, auto: bool):
        self.__func__ = func
        self.event_handler = event_handler
        self.origin = origin
        self.auto = auto

    def __eq__(self, other):
        return self.__func__ is other.__func__

    def __hash__(self):
        return hash(id(self.__func__))

    def make_weak_collection(self):
        return self.event_handler.make_weak_collection()

    def __getattr__(self, item):
        try:
            return super(FunctionStub, self).__getattr__(item)
        except AttributeError:
            pass
        return self.event_handler.__getattribute__(item)

    def __call__(self, *args, **kwargs):
        ret = None
        if self.origin:
            try:
                ret = self.__func__(*args, **kwargs)
            except AbortNotifyException as e:
                return e.return_value
        if self.auto:
            self.event_handler.mod_call(*args, **kwargs)
        return ret

    def duplicate(self) -> 'FunctionStub':
        return FunctionStub(self.__func__, self.event_handler.duplicate(), self.origin,self.auto)

    def switch_event_handler(self, event_handler: EventHandler):
        if type(event_handler) is type(self.event_handler):
            self.event_handler.update(event_handler)
        else:
            event_handler.update(self.event_handler)
            event_handler.pass_ref = self.event_handler.pass_ref
            event_handler.owner = self.event_handler.owner

    def __iadd__(self, other):
        self.event_handler.subscribe(other)
        return self

    def __isub__(self, other):
        self.event_handler.unsubscribe(other)
        return self


class BoundEvent(FunctionStub):
    __slots__ = '__self__', 'name'

    def __init__(self, obj_ref: object, func: Callable, event_handler: EventHandler, name: str, origin: bool, auto: bool):
        super(BoundEvent, self).__init__(func, event_handler, origin, auto)
        self.__self__ = obj_ref
        self.name = name

    def __call__(self, *args, **kwargs):
        return super(BoundEvent, self).__call__(self.__self__, *args, **kwargs)

    def duplicate(self) -> 'BoundEvent':
        return BoundEvent(self.__self__, self.__func__, self.event_handler.duplicate(), self.name, self.origin, self.auto)

    def switch_event_handler(self, event_handler: EventHandler):
        super(BoundEvent, self).switch_event_handler(event_handler)
        setattr(self.__self__, self.name, event_handler)

    def get_primitives(self):
        return self.name, self.origin, self.auto

    def set_primitives(self, auto, name, origin):
        self.auto = auto
        self.name = name
        self.origin = origin

    def emit(self, *args, **kwargs):
        self.event_handler.mod_call(self.__self__, *args, **kwargs)


class EventDescriptor:
    __slots__ = 'true_owner', 'origin', 'event_name', 'no_origin', 'bound_event_t', 'handler_t', 'auto', 'pass_ref'

    def __init__(self, stub: Callable, bound_event_t: Type[BoundEvent], event_name: str = None, no_origin=False,
                 handler_t=EventHandler, auto=True, pass_ref=1):
        if event_name is None:
            event_name = '_' + stub.__name__
        self.origin = stub
        self.event_name = event_name
        self.no_origin = no_origin
        self.bound_event_t = bound_event_t
        self.handler_t = handler_t
        self.auto = auto
        self.pass_ref = pass_ref

    def __set_name__(self, owner, name):
        if not hasattr(self, 'true_owner'):
            self.true_owner = owner

    def __get__(self, instance: object, owner: Type) -> BoundEvent | Callable:
        event_reg = self.event_name
        try:
            istc = getattr(instance, event_reg)
            if istc.owner is not self.true_owner:  # This is true when this is a super() call
                return partial(self.origin, instance)
        except AttributeError:
            istc = self.handler_t()
            istc.pass_ref = self.pass_ref
            istc.owner = self.true_owner
            setattr(instance, event_reg, istc)
        return self.bound_event_t(instance, self.origin, istc, event_reg, not self.no_origin, self.auto)


class SuperCopyDescriptor(EventDescriptor):
    __slots__ = tuple()

    def __init__(self, stub, **kwargs):
        self.origin = stub
        kwargs['bound_event_t'] = None
        self.event_name = kwargs

    def __set_name__(self, owner, name):
        bound_method: BoundEvent = getattr(super(owner, type('', (owner,), {'__init__': lambda x: None})()), name)
        descriptor: EventDescriptor = object.__getattribute__(bound_method.event_handler.owner, name)
        for sn, val in self.event_name.items():
            if val is None:
                self.__setattr__(sn, getattr(descriptor, sn))
            else:
                self.__setattr__(sn, val)
        super(SuperCopyDescriptor, self).__set_name__(owner, name)


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
            self.only = self.bound_event.event_handler.subs
            self.bound_event.event_handler.subs = self.bound_event.make_weak_collection()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.bound_event.update(self.only)


class WeakBoundEvent(WeakMethod):
    __slots__ = 'evh_name', 'prims'

    def __new__(cls, meth, callback=None):
        obj = super(WeakBoundEvent, cls).__new__(cls, meth, callback=callback)
        obj.evh_name = meth.name
        obj.prims = meth.get_primitives()
        return obj

    def __init__(self, meth, callback=None):
        super(WeakBoundEvent, self).__init__(meth, callback)

    def __call__(self):
        obj = super(WeakMethod, self).__call__()
        func = self._func_ref()
        evh_name = self.evh_name
        if (obj is None) or (func is None):
            return None
        return self._meth_type(obj, func, getattr(obj, evh_name), *self.prims)


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
                self.data.add(WeakBoundEvent(func, callback=self._remove))
            else:
                self.data.add(WeakMethod(func, self._remove))
        else:
            super(OrderedWeakSet, self).add(func)

    def remove(self, func: callable) -> None:
        if hasattr(func, '__self__'):
            if self._pending_removals:
                self._commit_removals()
            if isinstance(func, BoundEvent):
                self.data.remove(WeakBoundEvent(func))
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

