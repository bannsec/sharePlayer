import queue

class OrderedPriorityQueue(queue.PriorityQueue):
    """
    Implements a PriorityQueue that is sub-sorted using entry order. I.e.: everything else equal, the thing put into the queue first will go out first.
    """

    def __init__(self,maxsize=10):
        # The count is the critical part here
        self._count = 0

        # Call the constructor
        queue.PriorityQueue.__init__(self,maxsize=maxsize)

    def put(self,msg,priority):
        """
        This is where the magic is. Give a priority integer (lower is higher priority).
        """
        
        # Send it
        queue.PriorityQueue.put(self,(priority,self._count,msg))
        
        # Update our count
        self._count += 1
    
