import asyncio
from dataclasses import dataclass
from http.cookies import SimpleCookie
import logging
import time
import json
from traceback import print_exc
from typing import Any, List
from aiohttp import ClientResponse

from hugchat_api.core.Workflow import Workflow

from .Message import Message
from .Exceptions import *
from .config import RequestData, fillData, BASE_CONVERSATION
from hugchat_api.utils import Request

TYPE_STATUS = "status"
TYPE_STREAM = "stream"
TYPE_FINAL = "finalAnswer"
TYPE_WEB = "webSearch"


@dataclass
class Chatflow(Workflow):
    """
    single chat request
    """

    message: Message
    prompt: str
    conversation_id: str
    cookies: SimpleCookie[str]
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
        data = fillData(self.custom_data)
        data.inputs = self.prompt
        if self.message.web_search_enabled:
            data.web_search = True
        d = data.to_json()
        logging.debug(f"RequestData: {d}")
        return d

    async def parse(self, res: ClientResponse):
        """
        Parser for EventStream
        """
        if res.status != 200:
            raise Exception(f"chat fatal: {res.status} - {await res.text()}")
        reply = False
        try:
            size = 32
            tempchunk = ""
            tempbytes = b""
            # async for c in res.content.iter_chunked(size):
            while 1:
                c = await res.content.read(size)
                await asyncio.sleep(0)
                if not c:
                    break
                try:
                    dec = (tempbytes + c).decode("utf-8")
                    tempbytes = b""
                except Exception:
                    logging.debug(f"bytes decode error: {str(c)}")
                    tempbytes += c
                    continue
                lines = dec.splitlines()
                for line in lines:
                    if line:
                        # line = tempchunk + re.sub("^data:", "", line)
                        line = tempchunk + line
                        try:
                            js = json.loads(line)
                            tempchunk = ""
                        except Exception:
                            tempchunk = line
                            if '"type":"finalAnswer"' in tempchunk:
                                self.message.setText("", done=True)
                                break
                            logging.debug(f"js load error: {tempchunk}")
                            continue
                        try:
                            tp: str = js["type"]
                            logging.debug(js)
                            if tp == TYPE_STATUS:
                                if js[TYPE_STATUS] == "started":
                                    logging.debug("chat started")
                                else:
                                    logging.error(f"Status mismatch: {js['status']}")
                            elif tp == TYPE_WEB:
                                self.message.setWebSearchSteps(js)
                            elif tp == TYPE_STREAM:
                                self.message.setText(js["token"])
                                if not reply:
                                    reply = True
                            elif tp == TYPE_FINAL:
                                self.message.setFinalText(js["text"])
                                break
                            else:
                                logging.warning(f"Unrecognized response type: {tp}")
                        except Exception:
                            logging.error(f"JSON structure not recognized: {str(js)}")
            logging.debug("parse done")
            # logging.debug(await res.text())
            res.close()
            if not reply:
                raise Exception("No reply")
        except Exception as e:
            logging.debug("parse done with error")
            # logging.debug(await res.text())
            print_exc()
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
        logging.debug(f"request data: {self.custom_data}")
        flag = False
        for _ in range(self.max_tries):
            res = await Request.Post(url, cookies=self.cookies, data=data)
            logging.debug(f"Request status: {res.status}")
            if res.status != 200:
                logging.error("Internal error, may due to model overload, retrying...")
            else:
                flag = True
                break
            time.sleep(1)
            continue
        if not flag:
            self.message.setError(Exception("Request failed"))
            return
        err = await self.parseData(res)
        if not err:
            if self.callback is not None:
                self.callback[0](*self.callback[1])
        else:
            self.message.setError(err)
        return

    async def getWebSearch(self):
        return

    async def run(self):
        logging.debug(f"Start chat: {self.prompt}")
        # if self.message.web_search_enabled:
        #     await self.getWebSearch()
        try:
            await self.getReply()
        except Exception as e:
            self.message.setError(e)
