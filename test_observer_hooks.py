# - * -coding: utf - 8 - * -
"""
This file is disgusting. Don't read it.

@author: ☙ Ryan McConnell ♈♑ ❧
"""
import gc
import random

from observer_hooks import *
from observer_hooks.block_events import BlockSideEffects


class ImplicitSlots(object):
    __slots__ = ('aim', '_method', '__weakref__')

    def __init__(self):
        self.aim = 1
        self._method = EventHandler()

    def test(self):
        pass

    @notify()
    def method(self, arg: int) -> int:
        return arg


def test_duplicates_method():
    ows = OrderedWeakSet()
    impl = ImplicitSlots()
    ows.add(impl.test)
    assert impl.test in ows
    ows.add(impl.test)
    assert len(ows) == 1
    ows.remove(impl.test)
    assert impl.test not in ows
    assert len(ows) == 0

    class Something:
        def test(self):
            pass

    s = Something()
    ows.add(s.test)
    ows.add(s.test)
    assert len(ows) == 1
    ows.remove(s.test)
    assert len(ows) == 0

    def test_func():
        pass

    ows.add(test_func)
    assert test_func in ows

test_duplicates_method()

class ExtraImplicitSlots(object):
    __slots__ = ('aim', '_method', '__weakref__')

    def __init__(self):
        self.aim = 1

    @notify()
    def method(self, arg: int) -> int:
        return arg


class ExplicitSlots(object):
    __slots__ = ('aim', 'handler', '__weakref__')

    def __init__(self):
        self.aim = 1
        self.handler = EventHandler()

    @notify(event_name='handler')
    def method(self, arg: int) -> int:
        return arg


class Implicit(object):
    def __init__(self):
        self.aim = 1

    @notify()
    def method(self, arg: int) -> int:
        return arg


class Explicit(object):
    def __init__(self):
        self.aim = 1
        self.handler = EventHandler()

    @notify(event_name='handler')
    def method(self, arg: int) -> int:
        return arg


class NoOrigin(object):
    def __init__(self):
        self.aim = 1

    @notify(no_origin=True)
    def method(self, arg: int) -> int:
        raise AssertionError('Method called with no origin')


class FailureImplicit(object):
    def __init__(self):
        self.aim = 1
        self._method = None

    @notify()
    def method(self, arg: int) -> int:
        return arg


class SRmoteClass(object):
    def __init__(self):
        self.calls = []

    def hook_me(self, i: int):
        self.calls.append(i)
        return 0


def test_method_func(method):
    rand = random.randint(1, 100)
    assert rand == method()(rand)


def test_subscribe_static(method):
    local = []

    def hooked(f):
        local.append(f)
        return f + 5

    method().subscribe(hooked)
    assert 7 == method()(7)
    assert len(local) == 1
    assert local[0] == 7


def test_add_remove_static(method):
    local = []

    def hooked(f):
        local.append(f)
        return f + 5

    method().subscribe(hooked)
    rnd = random.randint(1, 100)
    assert rnd == method()(rnd)
    assert local[0] == rnd
    method().unsubscribe(hooked)
    rnd2 = random.randint(1, 100)
    assert rnd2 == method()(rnd2)
    assert len(local) == 1
    assert local[0] == rnd


def test_add_remove_dynamic(method):
    sr = SRmoteClass()
    assert len(sr.calls) == 0
    method().subscribe(sr.hook_me)
    rnd = random.randint(1, 100)
    assert rnd == method()(rnd)
    assert len(sr.calls) == 1
    assert sr.calls[0] == rnd
    method().unsubscribe(sr.hook_me)
    rnd2 = random.randint(1, 100)
    assert rnd2 == method()(rnd2)
    assert len(sr.calls) == 1
    assert sr.calls[0] == rnd


def test_garbage_collect_remove(method):
    sr = SRmoteClass()
    calls = sr.calls
    method().subscribe(sr.hook_me)
    rnd = random.randint(1, 100)
    assert len(sr.calls) == 0
    assert rnd == method()(rnd)
    assert len(sr.calls) == 1
    assert sr.calls[0] == rnd
    del sr
    gc.collect()
    rnd2 = random.randint(1, 100)
    assert rnd2 == method()(rnd2)
    assert len(calls) == 1
    assert calls[0] == rnd


def test_chain_call(method):
    class Proxynotify(object):
        def __init__(self):
            self.calls = []

        @notify()
        def hook_me(self, i: int):
            self.calls.append(i)
            return 0

    sr = Proxynotify()
    method().subscribe(sr.hook_me)
    global outer_flag
    try:
        outer_flag = False

        def some_hooked(hb:int):
            global outer_flag
            outer_flag = True
        sr.hook_me.subscribe(some_hooked)
        assert len(sr.calls) == 0
        assert not outer_flag
        rnd = random.randint(1, 100)
        assert rnd == method()(rnd)
        assert len(sr.calls) == 1
        assert sr.calls[0] == rnd
        assert outer_flag
    finally:
        del outer_flag


def test_subscribe_block_all(method):
    local = []

    def hooked(f):
        local.append(f)
        return f + 5

    method().subscribe(hooked)
    with BlockSideEffects(method()):
        assert 7 == method()(7)
    assert len(local) == 0
    assert len(method().event_handler.subs) == 1

    def hooked2(f):
        local.append(f)
        return f

    method().subscribe(hooked2)
    with BlockSideEffects(method()):
        assert 7 == method()(7)
    assert len(local) == 0
    assert len(method().event_handler.subs) == 2


def test_subscribe_block_selective(method):
    local = []

    def hooked(f):
        local.append(f)
        return f + 5

    method().subscribe(hooked)

    def hooked2(f):
        local.append(f)
        return f

    method().subscribe(hooked2)
    with BlockSideEffects(method(), only=(hooked,)):
        assert 7 == method()(7)
    assert len(local) == 1
    assert local[0] == 7
    assert len(method().event_handler.subs) == 2


def test_subscribe_block_selective_methods(method):
    local = []

    class Hok:
        def __init__(self, m):
            self.m = m
        def hooked(self, f):
            self.m.append(f)
            return f + 5

    class Hok2:
        def __init__(self, m):
            self.m = m

        def hooked(self, f):
            self.m.append(f)
            return f + 5
    hok = Hok(local)
    hok2 = Hok2(local)
    method().subscribe(hok.hooked)
    method().subscribe(hok2.hooked)

    with BlockSideEffects(method(), only=(hok.hooked,)):
        assert 7 == method()(7)
        assert len(method().event_handler.subs) == 1
    assert len(local) == 1
    assert local[0] == 7
    assert len(method().event_handler.subs) == 2


def test_no_autofire(method):
    local = []

    class Hok:
        def __init__(self, m):
            self.m = m

        @notify(auto_fire=False)
        def hooked(self, f):
            self.m.append(f)
            return f + 5

        def do_fire(self):
            self.hooked.emit(self, 99)

    def side_effect(h, num):
        h.m.append(num)

    hok = Hok(local)
    hok.hooked.subscribe(side_effect)
    method().subscribe(hok.hooked)

    assert 7 == method()(7)
    assert len(local) == 1
    assert local[0] == 7
    gc.collect()
    assert len(method().event_handler.subs) == 1
    hok.do_fire()
    assert len(local) == 2
    assert local[1] == 99


def test_emit_purge():
    global test_me
    test_me = False
    def hook(pt, rf):
        global test_me
        test_me = (pt == 5) and (rf == 'something')

    @notify()
    def hookable():
        assert test_me is False

    hookable.subscribe(hook)
    hookable.emit(5, 'something')
    assert test_me
    test_me = False
    hookable.purge()
    hookable()
    assert test_me is False

test_emit_purge()

def do_std(method):
    test_method_func(method)
    test_subscribe_static(method)
    test_add_remove_static(method)
    test_add_remove_dynamic(method)
    test_garbage_collect_remove(method)
    test_chain_call(method)
    test_subscribe_block_all(method)
    test_subscribe_block_selective(method)
    test_subscribe_block_selective_methods(method)
    test_no_autofire(method)


class TestingException(Exception): pass


def test_double_dip(cls, method, test_func=do_std):
    test_func(method)
    another = cls()

    def failure(*args, **kwargs):
        raise TestingException()

    another.method.subscribe(failure)
    try:
        test_func(method)
    except TestingException:
        raise AssertionError('Double dipped')
    try:
        test_func(lambda: another.method)
        raise AssertionError('Double dip failure case should fail')
    except TestingException:
        pass


for i in [Implicit, Explicit, ImplicitSlots, ExplicitSlots, ExtraImplicitSlots]:
    obj_ = i()
    test_double_dip(i, lambda: obj_.method)


def test_failure_implicit():
    someo = FailureImplicit()
    try:
        test_subscribe_static(lambda: someo.method)
        return AssertionError('Should have failed')
    except AttributeError:
        pass


test_failure_implicit()


def test_no_origin():
    no_orig = NoOrigin()
    no_orig.method(5)
    lis = []

    def test(intt: int):
        lis.append(intt)

    no_orig.method += test
    assert len(lis) == 0
    rnd = random.randint(1, 100)
    no_orig.method(rnd)
    assert len(lis) == 1
    assert lis[0] == rnd


test_no_origin()


def test_hooked_static_method():
    @notify()
    def static_method(arg: int) -> int:
        return arg

    do_std(lambda: static_method)


test_hooked_static_method()


def test_no_origin_method():
    class NoOriginTest:
        @notify(no_origin=True)
        def method(self):
            raise AssertionError('Calling method with no origin')

    someo = NoOriginTest()

    def test_no_origin_method_inner(method):
        global outer_flag
        try:
            outer_flag = False

            def some_hooked():
                global outer_flag
                outer_flag = True

            assert method()() == None
            assert not outer_flag
            method().subscribe(some_hooked)
            assert not outer_flag
            method()()
            assert outer_flag
        finally:
            del outer_flag
        test_double_dip(NoOriginTest, lambda: someo.method, test_func=test_no_origin_method_inner)


test_no_origin_method()

def test_static_method_chain():
    global outer_flag
    global outer_flag2
    global outer_flag3
    global outer_flag4
    try:
        outer_flag = False
        outer_flag2 = False
        outer_flag3 = False
        outer_flag4 = False

        @notify()
        def some_hooked():
            global outer_flag
            outer_flag = True

        @notify()
        def some_hooked2():
            global outer_flag2
            outer_flag2 = True

        @notify()
        def some_hooked3():
            global outer_flag3
            outer_flag3 = True

        def some_hooked4():
            global outer_flag4
            outer_flag4 = True

        assert not outer_flag
        assert not outer_flag2
        assert not outer_flag3
        some_hooked.subscribe(some_hooked2)
        some_hooked2.subscribe(some_hooked3)
        some_hooked3 += some_hooked4
        assert not outer_flag
        assert not outer_flag2
        assert not outer_flag3
        assert not outer_flag4
        some_hooked()
        assert outer_flag
        assert outer_flag2
        assert outer_flag3
        assert outer_flag4
    finally:
        del outer_flag
        del outer_flag2
        del outer_flag3
        del outer_flag4

test_static_method_chain()


def test_order_of_events():
    global order_observed
    order_observed = []
    try:
        @notify(no_origin=True)
        def some_hooked():
            pass

        def some_hooked2():
            global order_observed
            order_observed.append('some_hooked2')

        def some_hooked4():
            global order_observed
            order_observed.append('some_hooked4')

        def some_hooked3():
            global order_observed
            order_observed.append('some_hooked3')

        pairs = list((func, func.__name__) for func in {some_hooked2, some_hooked3, some_hooked4})
        random.shuffle(pairs)
        for func, _ in pairs:
            some_hooked += func
        assert len(order_observed) == 0
        some_hooked()
        assert len(order_observed) == 3
        for observed, ground in zip(order_observed, pairs):
            if observed != ground[1]:
                raise AssertionError(f'{observed} != {ground}')
    finally:
        del order_observed

for i in range(10):
    test_order_of_events()


def test_inheritance_modes():
    class A:
        @notify()
        def some_func(self, param):
            return 7

    class B(A):
        @notify()
        def some_func(self, param):
            raise AbortNotifyException(super(B, self).some_func(param))

    class C(B):
        pass

    class D(C):
        pass

    class E(D):
        @notify()
        def some_func(self, param):
            return super(E, self).some_func(param)

    class F(E):
        pass

    class G(F):
        @notify(auto_fire=False)
        def some_func(self, param):
            return super(G, self).some_func(param)

    def uoh(x):
        raise AssertionError()

    global gl
    gl = False

    def ok(x):
        global gl
        assert gl is False
        gl = True

    def tc(c):
        global gl
        b = c()
        print(c)
        b.some_func.subscribe(ok)

        gl = False
        assert b.some_func(99) == 7
        assert bool(gl)
        gl = False
        assert b.some_func(99) == 7
        assert bool(gl)

    def tf(c):
        global gl
        b = c()
        print(c)
        b.some_func.subscribe(ok)

        gl = False
        assert b.some_func(99) == 7
        assert gl is False

        gl = False
        assert b.some_func(99) == 7
        assert gl is False

    def all():
        for tt in (A, E, F):
            tc(tt)

        for tt in B, C, D:
            tf(tt)

    def test_manual_mode():
        global gl
        gl = False
        g = G()
        g.some_func.subscribe(ok)
        assert gl is False
        assert g.some_func(99) == 7
        assert gl is False
        assert g.some_func.emit(99) is None
        assert gl is True

    test_manual_mode()

test_inheritance_modes()


def test_lambda():
    class SomeClass:
        @notify(handler_t=HardRefEventHandler)
        def method(self):
            pass
    sv = []
    s = SomeClass()
    s.method.subscribe(lambda: sv.append(1))
    s.method()
    assert len(sv) == 1


def test_pas_ref():
    class SomeClass:
        @notify(pass_ref=True)
        def method(self):
            pass
    sv = []
    s = SomeClass()

    class SomeOtherClass:
        @notify()
        def method(self, other):
            sv.append(1)
            assert other is s

    b = SomeOtherClass()
    b.method.switch_event_handler(HardRefEventHandler())
    s.method.subscribe(b.method)
    b.method.subscribe(lambda x: sv.append(1))
    s.method()
    assert len(sv) == 2
test_pas_ref()
test_lambda()