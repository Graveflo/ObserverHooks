# - * -coding: utf - 8 - * -
"""


@author: ☙ Ryan McConnell ❧
"""
from unittest import TestCase, main

from observer_hooks import notify, EventCapturer


class TestEventCapture(TestCase):
    def get_handler(self):
        @notify()
        def some_func(*args, **kwargs):
            pass
        return some_func

    def test_empty(self):
        with EventCapturer(self.get_handler()) as e:
            pass
        self.assertFalse(e.captured_data)

    def test_single(self):
        ev = self.get_handler()
        with EventCapturer(ev) as e:
            ev(1)
        self.assertEqual(len(e.captured_data), 1)
        self.assertEqual(e.captured_data[0], (1, ))

    def test_multiple(self):
        ev = self.get_handler()
        with EventCapturer(ev) as e:
            for i in range(10):
                ev(i)
        self.assertEqual(len(e.captured_data), 10)
        for i in range(10):
            self.assertEqual(e.captured_data[i], (i,))

    def test_single_kwargs(self):
        ev = self.get_handler()
        with EventCapturer(ev) as e:
            ev(key=1)
        self.assertEqual(len(e.captured_data), 1)
        self.assertEqual(e.captured_data[0], {'key': 1})

    def test_multiple_kwargs(self):
        ev = self.get_handler()
        with EventCapturer(ev) as e:
            for i in range(10):
                ev(**{str(i): f'foo: {i}'})
        self.assertEqual(len(e.captured_data), 10)
        for i in range(10):
            self.assertEqual(e.captured_data[i], {str(i): f'foo: {i}'})

    def test_single_mixed(self):
        ev = self.get_handler()
        with EventCapturer(ev) as e:
            ev(1, key=1)
        self.assertEqual(len(e.captured_data), 1)
        self.assertEqual(e.captured_data[0], ((1,), {'key': 1}))

    def test_multiple_positional_and_keyword(self):
        ev = self.get_handler()
        with EventCapturer(ev) as e:
            ev(1, 2, '3', key=1, name=EventCapturer, foo='bar')
        self.assertEqual(len(e.captured_data), 1)
        self.assertEqual(e.captured_data[0], ((1,2,'3'), {'key': 1, 'name': EventCapturer, 'foo':'bar'}))

    def test_name(self):
        self.assertEqual(str(EventCapturer(self.get_handler())), 'EventCapture(test_event_capture.some_func)')


class TestMethodEventCapture(TestEventCapture):
    class ClassFoo:
        @notify()
        def bar(self, *args, **kwargs):
            pass

    def get_handler(self):
        return self.c.bar

    def setUp(self) -> None:
        self.c = self.ClassFoo()

    def tearDown(self) -> None:
        self.c = None

    def test_name(self):
        self.assertEqual(str(EventCapturer(self.get_handler())), 'EventCapture(ClassFoo.bar)')



if __name__ == '__main__':
    main()
