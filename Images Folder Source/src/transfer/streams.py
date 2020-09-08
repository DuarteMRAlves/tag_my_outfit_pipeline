from threading import Condition, Lock
from collections import deque


class RequestsStream:
    """
    Class to represent an object stream of requests
    This class is an iterator that blocks when there are no more requests
    unless complete is called, then the iterator will provide the remaining
    objects but wont accept any more requests
    """

    def __init__(self):
        self.__lock = Lock()
        self.__condition = Condition(lock=self.__lock)
        self.__requests: 'deque[object]' = deque()
        self.__accepting_requests: 'bool' = True

    def next(self, request: 'object'):
        with self.__lock:
            if self.__accepting_requests:
                self.__requests.append(request)
                self.__condition.notify_all()
            else:
                raise ValueError("Stream is closed")

    def complete(self):
        with self.__lock:
            self.__accepting_requests = False
            self.__condition.notify_all()

    def __next__(self):
        with self.__condition:
            while self.__accepting_requests and not self.__requests:
                self.__condition.wait()
            if not self.__requests:
                raise StopIteration()
            return self.__requests.popleft()

    def __iter__(self):
        return self
