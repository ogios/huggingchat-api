import asyncio
from threading import Thread
from concurrent.futures._base import Future

from hugchat_api.core.Workflow import Workflow
from .Exceptions import CoroutinThreadErr


class CorotineLoop:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.thread = Thread(
            target=self._run_loop,
            daemon=True,
            name="async_loop"
        )
        self.thread.start()

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def _checkThread(self):
        return self.thread.is_alive()

    async def _run(self, flow: Workflow):
        return await flow.run()

    def submit(self, flow: Workflow) -> Future[None]:
        if self._checkThread():
            fut = asyncio.run_coroutine_threadsafe(self._run(flow), self.loop)
            return fut
        else:
            raise CoroutinThreadErr("Thread is Down")
        
