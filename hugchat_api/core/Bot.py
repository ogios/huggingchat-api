import logging
import time
import uuid
import requests
import requests.utils
import requests.sessions
import json
import re
from typing import Callable, Tuple

from .WebSearch import WebSearch
from .Message import Message
from .ThreadPool import ThreadPool
from ..utils import getTime
from .Exceptions import *
from . import ListBots




class Bot:
    def __init__(
            self,
            email: str,
            cookies: requests.sessions.RequestsCookieJar,
            thread_pool: ThreadPool,
            model: str = ListBots.FALCON_180B,
    ):
        self.thread_pool: ThreadPool = thread_pool
        self.email = email
        self.model = model
        self.default_params = {
            "temperature": 0.9,
            "top_p": 0.95,
            "repetition_penalty": 1.2,
            "top_k": 50,
            "truncate": 1024,
            "watermark": False,
            "max_new_tokens": 1024,
            "stop": [
                "</s>"
            ],
            "return_full_text": False
        }
        self.url_index = "https://huggingface.co/chat/"
        self.url_initConversation = "https://huggingface.co/chat/conversation"
        self.headers = {
            "Referer": "https://huggingface.co/chat",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36 Edg/112.0.1722.64",
        }
        self.cookies = cookies
        # self.conversations = list()
        self.conversations = dict()
        self.current_conversation = None
        self.fetchConversations()
    
    def fetchConversations(self):
        """
        Get conversation a from a html and extract them using re
        """
        logging.info("Fetching all conversations...")
        self.conversations = dict()
        res = self._requestsGet(self.url_index)
        html = res.text
        conversation_ids = list(set(re.findall('href="/chat/conversation/(.*?)"', html)))
        for i in conversation_ids:
            title = re.findall(f'href="/chat/conversation/{i}.*?<div class="flex-1 truncate">(.*?)</div>', html, re.S)
            if len(title) > 0:
                title = title[0].strip()
            else:
                title = "Untitled conversation"
            self.conversations[i] = title
            # self.conversations.append({"id": i, "title": title})
    
    def _requestsGet(self, url: str, params=None, stream=False) -> requests.Response:
        """
        GET
        """
        res = requests.get(
            url,
            params=params,
            headers=self.headers,
            cookies=self.cookies,
            stream=stream,
            # verify=False,
        )
        return res
    
    def _requestsPost(self, url: str, headers=None, params=None, data=None, stream=False) -> requests.Response:
        """
        POST
        """
        res = requests.post(
            url,
            stream=stream,
            params=params,
            data=data,
            headers=self.headers if not headers else headers,
            cookies=self.cookies,
            # verify=False,
        )
        return res
    
    def _getUUID(self):
        """
        random uuid
        :return:  hex with the format '8-4-4-4-12'
        """
        uid = uuid.uuid4().hex
        return f"{uid[:8]}-{uid[8:12]}-{uid[12:16]}-{uid[16:20]}-{uid[20:]}"
    
    def customizeData(
            self,
            temperature: float = 0.9,
            top_p: float = 0.95,
            repetition_penalty: float = 1.2,
            top_k: int = 50,
            truncate: int = 1024,
            watermark: bool = False,
            max_new_tokens: int = 1024,
            return_full_text: bool = False
    ):
        return {
            "temperature": temperature,
            "top_p": top_p,
            "repetition_penalty": repetition_penalty,
            "top_k": top_k,
            "truncate": truncate,
            "watermark": watermark,
            "max_new_tokens": max_new_tokens,
            "stop": [
                "</s>"
            ],
            "return_full_text": return_full_text
        }
    
    def _getData(self, text, web_search_id: str = "", params: dict = None):
        """
        Default data
        """
        web_search_id = "" if not web_search_id else web_search_id
        data = {
            "inputs": text,
            "parameters": params if params else self.default_params,
            "options": {
                "id": self._getUUID(),
                "response_id": self._getUUID(),
                "is_retry": False,
                "use_cache": False,
                "web_search_id": web_search_id
            },
            "stream": True,
        }
        return data
    
    def __parseData(self, res: requests.Response, message: Message):
        """
        Parser for EventStream
        """
        if res.status_code != 200:
            raise Exception(f"chat fatal: {res.status_code} - {res.text}")
        reply = None
        for c in res.iter_content(chunk_size=1024):
            chunks = c.decode("utf-8").split("\n\n")
            tempchunk = ""
            for chunk in chunks:
                if chunk:
                    chunk = tempchunk + re.sub("^data:", "", chunk)
                    try:
                        js = json.loads(chunk)
                        tempchunk = ""
                    except:
                        tempchunk = chunk
                        continue
                    try:
                        if (js["token"]["special"] == True) & (js["generated_text"] != None):
                            reply = js["generated_text"]
                            message.setFinalText(reply)
                        else:
                            reply = js["token"]["text"]
                            message.setText(reply)
                    except:
                        logging.error(str(js))
                        # print(js)
        res.close()
        return reply
    
    def _parseData(self, res: requests.Response, message: Message):
        try:
            reply = self.__parseData(res, message)
            if not reply:
                raise Exception("No reply")
        except Exception as e:
            # message.setError(e)
            return e
        return None
    
    def _getReply(
            self,
            conversation_id: str,
            text: str,
            message: Message,
            web_search_id: str = "",
            max_tries: int = 3,
            callback: Tuple[Callable, tuple] = None
    ):
        """
        Send message and Parse response
        """
        url = self.url_initConversation + f"/{conversation_id}"
        exp = Exception("No reply")
        data = self._getData(text, web_search_id)
        for i in range(max_tries):
            res = self._requestsPost(url, stream=True, data=json.dumps(data))
            if res.status_code == 500:
                logging.error("Internal error, may due to model overload, retrying...")
            else:
                exp = self._parseData(res, message=message)
                if not exp:
                    if not self.conversations[conversation_id]:
                        self.updateTitle(conversation_id)
                    if callback != None:
                        callback[0](*callback[-1])
                    return
            time.sleep(1)
            continue
        message.setError(exp)
    
    def _chatWeb(
            self,
            conversation_id: str,
            text: str,
            message: Message,
            web_search_id: str = "",
            max_tries: int = 3,
            callback: Tuple[Callable, tuple] = None
    ):
        
        webUrl = self.url_initConversation + f"/{conversation_id}/web-search"
        js = WebSearch(
            webUrl + f"?prompt={text}",
            self.cookies.get_dict(),
            conversation_id,
            message
        ).getWebSearch()
        web_search_id = js["messages"][-1]["id"] if js else ""
        logging.info(f"web_search_id: {web_search_id}")
        
        self._getReply(conversation_id, text, message, web_search_id, max_tries, callback=callback)
    
    def chat(self, text: str, conversation_id=None, web_search=False, max_tries: int = 3, callback: Tuple[Callable, tuple] = None) -> Message:
        """
        Normal chat, send message and wait for reply
        """
        conversation_id = self.current_conversation if not conversation_id else conversation_id
        if not conversation_id:
            logging.info("No conversation selected")
            return None
        message = Message(conversation_id, web_search)
        
        if web_search:
            self.thread_pool.submit(self._chatWeb, (conversation_id, text, message, "", max_tries, callback))
        else:
            self.thread_pool.submit(self._getReply, (conversation_id, text, message, "", max_tries, callback))
        return message
    
    def updateTitle(self, conversation_id) -> str:
        """
        Get conversation summary
        """
        if not self.conversations.__contains__(conversation_id):
            raise ConversationNotExistError(f"The given conversation is not in the map: {conversation_id}")
        url = self.url_initConversation + f"/{conversation_id}/summarize"
        res = self._requestsPost(url)
        if res.status_code != 200:
            raise Exception("get conversation title failed")
        js = res.json()
        self.conversations[conversation_id] = js["title"]
        # for i in range(len(self.conversations)):
        #     if self.conversations[i]["id"] == conversation_id:
        #         self.conversations[i]["title"] = js["title"]
        #         break
        return js["title"]
    
    def createConversation(self) -> str:
        """
        start a new conversation
        """
        data = {"model": self.model}
        res = self._requestsPost(self.url_initConversation, data=json.dumps(data))
        if res.status_code != 200:
            raise Exception("create conversation fatal")
        js = res.json()
        conversation_id = js["conversationId"]
        # message = self.chat(text, conversation_id, web=web)
        self.conversations[conversation_id] = None
        # conversation = {"id": conversation_id, "title": "None"}
        # self.conversations.append(conversation)
        self.current_conversation = conversation_id
        return conversation_id
    
    def removeConversation(self, conversation_id: str):
        """
        Remove conversation through the index of self.conversations
        """
        if not self.conversations.__contains__(conversation_id):
            raise ConversationNotExistError(f"The given conversation is not in the map: {conversation_id}")
        logging.info(f"Deleting conversation <{conversation_id}>")
        url = self.url_initConversation + f"/{conversation_id}"
        res = requests.delete(url, headers=self.headers, cookies=self.cookies)
        if res.status_code != 200:
            logging.info(f"{res.text}")
            logging.info("Delete conversation fatal")
            raise Exception("Delete conversation fatal")
        del self.conversations[conversation_id]
        if self.current_conversation == conversation_id:
            self.current_conversation = None
    
    def _getHistoriesByID(self, conversation_id):
        """
        :return: [{
            "conversation_id"
            "is_user"
            "text"
            "text_id"
        }]
        """
        histories = []
        url = self.url_initConversation + f"/{conversation_id}/__data.json?x-sveltekit-invalidated=_1"
        res = self._requestsGet(url)
        if res.status_code != 200:
            return None
        data = res.json()["nodes"]
        history = None
        for dic in data:
            if dic.__contains__("data"):
                history = dic["data"]
        if history:
            for his in history:
                if isinstance(his, dict):
                    if his.__contains__("content"):
                        histories.append({
                            "conversation_id": conversation_id,
                            "is_user": 1 if history[his["from"]] == "user" else 0,
                            "text": history[his["content"]],
                            "text_id": history[his["id"]],
                        })
        return histories
    
    def getHistoriesByID(self, conversation_id=None) -> list:
        conversation_id = self.current_conversation if not conversation_id else conversation_id
        if not conversation_id:
            return []
        logging.info(f"Getting histories for {self.email}:{conversation_id}...")
        histories = self._getHistoriesByID(conversation_id)
        if histories == None:
            raise Exception("Something went wrong")
        else:
            return histories
    
    def getConversations(self) -> dict:
        return self.conversations
    
    def switchConversation(self, conversation_id: str):
        if not self.conversations.__contains__(conversation_id):
            raise ConversationNotExistError(f"The given conversation is not in the map: {conversation_id}")
        self.current_conversation = conversation_id


if __name__ == "__main__":
    pass
