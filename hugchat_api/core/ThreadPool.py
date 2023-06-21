import time
import traceback
import os
from threading import Thread
from typing import List, Callable


class ThreadPool:
    def __init__(self, max_workers: int = 3):
        self.max_workers = max_workers
        self.wait_line: List[Thread] = []
        self.on_going: List[Thread] = []
        self.error = None
        Thread(target=self._manage, daemon=True).start()
    
    def _manage(self):
        try:
            while 1:
                while len(self.on_going) < self.max_workers:
                    if len(self.wait_line) == 0:
                        break
                    thread = self.wait_line[0]
                    del self.wait_line[0]
                    thread.start()
                    self.on_going.append(thread)
                for thread in self.on_going:
                    if not thread.is_alive():
                        index = self.on_going.index(thread)
                        del self.on_going[index]
                time.sleep(0.2)
        except Exception as e:
            self.error = e
            traceback.print_exc()
            os._exit(0)
    
    def submit(self, func: Callable, params: tuple = tuple()):
        self.wait_line.append(Thread(target=func, args=params, daemon=True))
