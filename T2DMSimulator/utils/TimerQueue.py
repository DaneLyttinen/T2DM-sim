import heapq

class TimerQueue:
    def __init__(self):
        self.heap = []
        self.counter = 0 

    def put(self, item, priority):
        heapq.heappush(self.heap, (priority, self.counter, item))
        self.counter += 1

    def get(self):
        self.heap = [(priority-5, count, item) for priority, count, item in self.heap]
        heapq.heapify(self.heap)

        if self.heap and self.heap[0][0] <= 0:
            _, _, item = heapq.heappop(self.heap)
            return item
        return None

    def peek(self):
        if self.heap:
            return self.heap[0][2]
        return None

    def is_empty(self):
        return len(self.heap) == 0

    def size(self):
        return len(self.heap)
