from concurrent.futures import Future
from typing import Callable
import time
import logging
from hugchat_api.core.Workflow import Workflow


class Customflow(Workflow):
    @staticmethod
    def wait(fut: Future):
        """
        Wait for the `Future` to be Done.
        To be noticed: The Exception will be raised if there is one.
        """
        while not fut.done():
            time.sleep(0.01)
        logging.debug(f"Wait future done: {fut}")
        return fut.result()

    @staticmethod
    def wrap(func: Callable):
        c = Customflow()
        c.run = func
        return c

    async def run(self):
        pass
