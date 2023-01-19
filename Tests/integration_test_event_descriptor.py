# - * -coding: utf - 8 - * -
"""


@author: ☙ Ryan McConnell ❧
"""
from types import FunctionType
from unittest import TestCase, main

from observer_hooks import notify, EventDescriptor, EventHandler


class TestEventDescriptorIntegration(TestCase):
    def test_switch_event_handler_no_kill_descriptor(self):
        class Foo:
            @notify()
            def some_method(self):
                pass

            def other_method(self):
                pass

        # preamble proof of concept
        f = Foo()
        self.assertNotIn('other_method', f.__dict__)
        f.other_method = f.other_method
        self.assertIn('other_method', f.__dict__)  # bad

        # actual test
        f = Foo()
        self.assertNotIn('some_method', f.__dict__)
        f.some_method.switch_event_handler(EventHandler())
        self.assertNotIn('some_method', f.__dict__)  # not bad


if __name__ == '__main__':
    main()
