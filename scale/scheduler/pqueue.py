
'A priority queue which prevents starvation through aging.'

import Queue
import heapq


class FairPriorityQueue(Queue.PriorityQueue):
    '''A PriorityQueue that prevents starvation through aging.
    '''

    def age(self):
        '''Age all items in the queue then rebalance.

        Maximum age is the length of the queue preventing early promotion of
        items for large queues.
        '''
        self.queue = map(lambda s, ma=self.qsize(): s.age(ma), self.queue)
        heapq.heapify(self.queue)

    def get(self, block=True, timeout=None):
        rval = Queue.PriorityQueue.get(self, block, timeout)
        self.age()
        return rval


class Item(object):
    '''An item for the FairPriorityQueue which ages to
       promote priority and prevent starvation.'''

    def __init__(self, priority):
        '''Initialize a new Item.

           :param priority: The priority of the item.
                            Lower numbers process first.
                            Minimum value is 0.
           :type priority: int
        '''
        assert priority >= 0
        self.__priority, self.__age = priority, 0

    def __repr__(self):
        return "<pqueue.Item priority %d age %d>" % (self.priority, self.__age)

    def age(self, max_age):
        '''Increase the age of the item.
           If the item is older than max_age decrease the
           priority value and reset the age.
           The minimum priority value is 0.

           :param max_age: The maximum age before promotion.
           :type max_age: int
           :returns: self so this can be used in a map()
           :rtype: Item
        '''
        self.__age += 1
        if self.__age >= max_age:
            self.__age = 0
            if self.__priority >= 0:
                self.__priority -= 1
        return self

    @property
    def priority(self):
        '''Access the current priority.
           :returns: The current priority
           :rtype: int
        '''
        return self.__priority

    def __cmp__(self, other):
        '''Commpare method.
           :param other: The other Item to compare
           :type other: Item
           :returns: cmp() compatible return based on the Item priority
           :rtype: int
        '''
        return cmp(self.priority, other.priority)
