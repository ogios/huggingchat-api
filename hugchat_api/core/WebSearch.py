from http.cookies import SimpleCookie
import json
import time
import logging
import traceback
import urllib3.util
from aiohttp import ClientResponse

from .Message import Message
from hugchat_api.utils import Request


class WebSearch:
    def __init__(
        self,
        url: str,
        cookies: SimpleCookie[str],
        conversation_id: str,
        message: Message,
    ):
        self.data = None
        self.url = urllib3.util.parse_url(url).url
        self.headers = {
            "Referer": self.url,
            "Connection": "close",
            "Cache-Control": "max-age=0",
            "Accept": "*/*",
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.143 Safari/537.36",
            "Accept-Language": "zh-CN,zh;q=0.8",
        }
        self.cookies = cookies
        self.conversation_id = conversation_id
        self.index = -1
        self.message = message

    async def parseWebData(self, res: ClientResponse):
        if res.status != 200:
            raise Exception("chat fatal")
        # index = -1
        start = time.time()
        try:
            tempchunk = ""
            async for c in res.content.iter_chunked(1024):
                chunks = c.decode("utf-8").splitlines()
                if len(chunks) > 1:
                    tempchunk = ""
                for chunk in [chunks[-1]]:
                    if chunk:
                        try:
                            chunk = tempchunk + chunk
                            js = json.loads(chunk)
                            self.message.setWebSearchSteps(js)
                            tempchunk = ""
                        except Exception:
                            tempchunk = chunk
                            logging.info(f"load fatal: {chunk}")
                            continue
                        try:
                            if js["messages"][-1]["type"] == "result":
                                # self.message.setWebSearchSteps(js["messages"][-1])
                                self.message.web_search_done = True
                                res.close()
                                return js
                            # elif len(js["messages"]) - 1 > index:
                            #   if index == -1:
                            #       index = 0
                            #   for message in js["messages"][index+1:]:
                            #       self.message.setWebSearchSteps(message)
                            #       index += 1
                        except Exception:
                            pass
        except Exception as e:
            logging.error(str(e))
            traceback.print_exc()
        print(f"web_search consumes: {time.time()-start}")
        res.close()
        return None

    async def getWebSearch(self):
        res = await Request.Get(self.url, headers=self.headers, cookies=self.cookies)
        try:
            data = await self.parseWebData(res)
            return data
        except Exception as e:
            logging.error(str(e))
            traceback.format_exc()
            self.message.setError(e)
            raise e

    # def _parseData(self, data):
    #   try:
    #       data = data.decode("utf-8")
    #       js = json.loads(data)
    #       self.data = js
    #       messages = js["messages"]
    #       self.message.setWebSearchSteps(self.data)
    #       if messages[-1]["type"] == "result":
    #           # self.message.setWebSearchSteps(self.data)
    #           # self.WSOut.sendWebSearch(messages[-1], conversation_id=self.conversation_id)
    #           return 456
    #       elif len(messages) - 1 > self.index:
    #           if self.index == -1:
    #               # self.message.setWebSearchSteps(self.data)
    #               # self.WSOut.sendWebSearch(messages[0], conversation_id=self.conversation_id)
    #               self.index = 0
    #           for message in messages[self.index + 1:]:
    #               # self.message.setWebSearchSteps(self.data)
    #               # self.WSOut.sendWebSearch(message, conversation_id=self.conversation_id)
    #               self.index += 1
    #   except (JSONDecodeError, json.JSONDecodeError):
    #       logging.error(
    #           "One error occurred when parsing WebSearch data, it's fine since it sometimes returns responses in a wrong json format"
    #       )
    #   except Exception as e:
    #       logging.error(str(e))
    #       traceback.format_exc()
    #
    #
    # def _getWebSearch(self):
    #
    #   self.c.setopt(pycurl.URL, self.url)
    #   self.c.setopt(pycurl.REFERER, self.url)
    #   self.c.setopt(pycurl.HTTPHEADER, [
    #       'Connection: close', 'Cache-Control: max-age=0',
    #       'Accept: */*',
    #       'User-Agent: Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.143 Safari/537.36',
    #       'Accept-Language: zh-CN,zh;q=0.8'
    #   ])
    #   self.c.setopt(pycurl.HTTP_VERSION, pycurl.CURL_HTTP_VERSION_1_0)
    #   self.c.setopt(pycurl.COOKIE, dictToString(self.cookies))
    #   # self.c.setopt(pycurl.VERBOSE, True)
    #   self.c.setopt(pycurl.WRITEFUNCTION, self.parseData)
    #   try:
    #       self.c.perform()
    #   except Exception as e:
    #       self.c.close()
    #       if e.args[0] != 23:
    #           self.message.setError(e)
    #           raise e
    #   self.c.close()
    #   return self.data

    def getSearchData(self):
        return self.data


if __name__ == "__main__":
    pass
