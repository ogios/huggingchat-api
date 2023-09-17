from dataclasses import dataclass
from http.cookies import SimpleCookie
import logging
import time
import json
import re
from typing import Any, List
from aiohttp import ClientResponse

from hugchat_api.core.Workflow import Workflow

from .WebSearch import WebSearch
from .Message import Message
from .Exceptions import *
from .config import RequestData, fillData, BASE_CONVERSATION
from hugchat_api.utils import Request


@dataclass
class Chatflow(Workflow):
    """
    single chat request
    """

    message: Message
    prompt: str
    conversation_id: str
    cookies: SimpleCookie[str]
    web_search_id: str = ""
    custom_data: RequestData | None = None
    max_tries: int = 3
    callback: List[Any] | None = None
    """
    [
        <function>Callable,
        <args>List[any]
    ]
    """

    def getRequestData(self):
        """
        Fill the custom data with defaults
        """
        web_search_id = "" if not self.web_search_id else self.web_search_id
        data = fillData(self.custom_data)
        data.inputs = self.prompt
        data.options.web_search_id = web_search_id
        return data.to_json()

    async def parse(self, res: ClientResponse):
        """
        Parser for EventStream
        """
        if res.status != 200:
            raise Exception(f"chat fatal: {res.status} - {await res.text()}")
        reply = None
        try:
            tempchunk = ""
            async for c in res.content.iter_chunked(1024):
                chunks = c.decode("utf-8").split("\n\n")
                for chunk in chunks:
                    if chunk:
                        chunk = tempchunk + re.sub("^data:", "", chunk)
                        try:
                            js = json.loads(chunk)
                            tempchunk = ""
                        except Exception:
                            logging.error("shit")
                            tempchunk = chunk
                            continue
                        try:
                            if (js["token"]["special"] is True) & (
                                js["generated_text"] is not None
                            ):
                                reply = js["generated_text"]
                                self.message.setFinalText(reply)
                            else:
                                reply = js["token"]["text"]
                                self.message.setText(reply)
                        except Exception:
                            logging.error(str(js))
                            # print(js)
            res.close()
            if not reply:
                raise Exception("No reply")
        except Exception as e:
            res.close()
            raise e

    async def parseData(self, res: ClientResponse):
        try:
            await self.parse(res)
        except Exception as e:
            logging.error(e)
            self.message.setError(e)
            self.message.done = True
            return e
        return None

    async def getReply(self):
        """
        Send message and Parse response
        """
        url = f"{BASE_CONVERSATION}/{self.conversation_id}"
        err = Exception("No reply")
        data = self.getRequestData()
        for _ in range(self.max_tries):
            res = await Request.Post(url, cookies=self.cookies, data=data)
            if res.status == 500:
                logging.error("Internal error, may due to model overload, retrying...")
            else:
                err = await self.parseData(res)
                if not err:
                    if self.callback is not None:
                        self.callback[0](*self.callback[1])
                    return
            time.sleep(1)
            continue
        self.message.setError(err)
        return

    async def getWebSearch(self):
        web_url = f"{BASE_CONVERSATION}/{self.conversation_id}/web-search"
        js = await WebSearch(
            web_url + f"?prompt={self.prompt}",
            self.cookies,
            self.conversation_id,
            self.message,
        ).getWebSearch()
        if not js:
            logging.error("Web search seems to met some problems, start chat without web search...")
        web_search_id = js["messages"][-1]["id"] if js else ""
        logging.info(f"web_search_id: {web_search_id}")
        self.web_search_id = web_search_id
        return

    async def run(self):
        if self.message.web_search_enabled:
            await self.getWebSearch()
        await self.getReply()
