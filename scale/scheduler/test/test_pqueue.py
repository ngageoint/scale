#@PydevCodeAnalysisIgnore
from django.test import TestCase

from scheduler import pqueue


class PQueueTests(TestCase):

    def test_item(self):
        a = pqueue.Item(5)
        self.assertEqual(a.priority, 5, "Priority access failed")

        a.age(2)
        self.assertEqual(a.priority, 5, "Failed to age")

        a.age(2)
        self.assertEqual(a.priority, 4, "Failed to age")
        self.assertEqual(a, pqueue.Item(4), "Comparison == failed")
        self.assertLess(a, pqueue.Item(5), "Comparison < failed")
        self.assertGreater(a, pqueue.Item(3), "Comparison > failed")

    def test_queue(self):
        q = pqueue.FairPriorityQueue()
        a, b = pqueue.Item(2), pqueue.Item(5)
        a.foo, b.foo = 'a', 'b'
        q.put(a)
        q.put(b)

        for x in ['c', 'd', 'z']:
            tmp = pqueue.Item(1)
            tmp.foo = x
            q.put(tmp)
            tmp2 = q.get()
            if x == 'z':
                self.assertEqual(a.foo, tmp2.foo, "Invalid aging")
            else:
                self.assertEqual(tmp.foo, tmp2.foo, "Invalid get()")
