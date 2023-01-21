from unittest import TestCase

from observer_hooks import notify, HardRefEventHandler


class TestSupportedOddities(TestCase):
    def test_add_while_iterating(self):
        for i in range(10):
            order = []

            @notify(handler_t=HardRefEventHandler)
            def master():
                pass

            def sub1():
                order.append('sub1')
                master.subscribe(sub3)

            master.subscribe(sub1)

            for _ in range(i):
                def sub2():
                    order.append('sub2')

                master.hard_subscribe(sub2)

            def sub3():
                order.append('sub3')

            master()
            lis = ['sub2'] * i
            lis.insert(0, 'sub1')
            lis.append('sub3')
            self.assertListEqual(lis, order, msg=f'failure index {str(i)}')
