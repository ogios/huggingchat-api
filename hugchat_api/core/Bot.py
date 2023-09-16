import logging
import time
from typing import Dict
import requests
import requests.utils
import requests.sessions
import json
import re

from .WebSearch import WebSearch
from .Message import Message
from .ThreadPool import ThreadPool
from .Exceptions import *
from . import ListBots
from .config import RequestData, fillData
from hugchat_api.utils import Request


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
        self.url_index = "https://huggingface.co/chat/"
        self.url_initConversation = "https://huggingface.co/chat/conversation"
        self.cookies = cookies
        # self.conversations = list()
        self.conversations: Dict[str, str] = dict()
        self.current_conversation = None
        self.fetchConversations()

    def fetchConversations(self):
        """
        Get conversation a from a html and extract them using re
        """
        logging.info("Fetching all conversations...")
        self.conversations = dict()
        res = Request.Get(self.url_index, self.cookies)
        html = res.text
        conversation_ids = list(
            set(re.findall('href="/chat/conversation/(.*?)"', html))
        )
        for i in conversation_ids:
            title = re.findall(
                f'href="/chat/conversation/{i}.*?<div class="flex-1 truncate">(.*?)</div>',
                html,
                re.S,
            )
            if len(title) > 0:
                title = title[0].strip()
            else:
                title = "Untitled conversation"
            self.conversations[i] = title
            # self.conversations.append({"id": i, "title": title})


    def _getData(
        self, text, web_search_id: str = "", provide_data: RequestData | None = None
    ):
        """
        Fill the custom data with defaults
        """
        web_search_id = "" if not web_search_id else web_search_id
        data = fillData(provide_data)
        data.inputs = text
        data.options.web_search_id = web_search_id
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
                    except Exception:
                        tempchunk = chunk
                        continue
                    try:
                        if (js["token"]["special"] is True) & (
                            js["generated_text"] is not None
                        ):
                            reply = js["generated_text"]
                            message.setFinalText(reply)
                        else:
                            reply = js["token"]["text"]
                            message.setText(reply)
                    except Exception:
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
    ):
        """
        Send message and Parse response
        """
        url = self.url_initConversation + f"/{conversation_id}"
        err = Exception("No reply")
        data = self._getData(text, web_search_id)
        for _ in range(max_tries):
            res = Request.Post(
                url, cookies=self.cookies, stream=True, data=json.dumps(data)
            )
            if res.status_code == 500:
                logging.error("Internal error, may due to model overload, retrying...")
            else:
                err = self._parseData(res, message=message)
                if not err:
                    if not self.conversations[conversation_id]:
                        self.updateTitle(conversation_id)
                    return
            time.sleep(1)
            continue
        message.setError(err)

    def _chatWeb(
        self,
        conversation_id: str,
        text: str,
        message: Message,
        web_search_id: str = "",
        max_tries: int = 3,
    ):
        webUrl = self.url_initConversation + f"/{conversation_id}/web-search"
        js = WebSearch(
            webUrl + f"?prompt={text}",
            self.cookies.get_dict(),
            conversation_id,
            message,
        ).getWebSearch()
        web_search_id = js["messages"][-1]["id"] if js else ""
        logging.info(f"web_search_id: {web_search_id}")

        self._getReply(conversation_id, text, message, web_search_id, max_tries)

    def chat(
        self,
        text: str,
        conversation_id=None,
        web_search=False,
        max_tries: int = 3,
    ) -> Message | None:
        """
        Normal chat, send message and wait for reply
        """
        conversation_id = (
            self.current_conversation if not conversation_id else conversation_id
        )
        if not conversation_id:
            logging.info("No conversation selected")
            return None
        message = Message(conversation_id, web_search)

        if web_search:
            self.thread_pool.submit(
                self._chatWeb, (conversation_id, text, message, "", max_tries)
            )
        else:
            self.thread_pool.submit(
                self._getReply,
                (conversation_id, text, message, "", max_tries),
            )
        return message

    def updateTitle(self, conversation_id) -> str:
        """
        Get conversation summary
        """
        if not self.conversations.__contains__(conversation_id):
            raise ConversationNotExistError(
                ConversationNotExistError.NotInMap.replace("--id--", conversation_id)
            )
        # request for title
        url = self.url_initConversation + f"/{conversation_id}/summarize"
        res = Request.Post(url, cookies=self.cookies)
        if res.status_code != 200:
            raise Exception("get conversation title failed")
        js = res.json()

        # set title in map
        self.conversations[conversation_id] = js["title"]
        return js["title"]

    def createConversation(self) -> str:
        """
        Start a new conversation
        """

        # Create new empty conversation
        # with model defined
        data = {"model": self.model}
        res = Request.Post(
            self.url_initConversation, cookies=self.cookies, data=json.dumps(data)
        )
        if res.status_code != 200:
            raise Exception("create conversation fatal")
        js = res.json()

        # add conversation id(key) to map
        # and set title to None
        conversation_id = js["conversationId"]
        self.conversations[conversation_id] = None
        self.current_conversation = conversation_id
        return conversation_id

    def removeConversation(self, conversation_id: str):
        """
        Remove conversation through the index of self.conversations
        """
        if not self.conversations.__contains__(conversation_id):
            raise ConversationNotExistError(
                ConversationNotExistError.NotInMap.replace("--id--", conversation_id)
            )
        logging.info(f"Deleting conversation <{conversation_id}>")

        # Request for delete
        url = self.url_initConversation + f"/{conversation_id}"
        res = Request.Delete(url, cookies=self.cookies)
        if res.status_code != 200:
            logging.info(f"{res.text}")
            logging.info("Delete conversation fatal")
            raise Exception("Delete conversation fatal")

        # delete it in map
        del self.conversations[conversation_id]
        if self.current_conversation == conversation_id:
            self.current_conversation = None

    def _getHistoriesByID(self, conversation_id):
        """
        :return:
        [
            {
                "conversation_id"
                "is_user"
                "text"
                "text_id"
            }
        ]
        """
        histories = []

        # Get all histories
        url = (
            self.url_initConversation
            + f"/{conversation_id}/__data.json?x-sveltekit-invalidated=_1"
        )
        res = Request.Get(url, cookies=self.cookies)
        if res.status_code != 200:
            return None

        # Check if histories exists
        data = res.json()["nodes"]
        history = None
        for dic in data:
            if dic.__contains__("data"):
                history = dic["data"]

        # Parse histories
        if history:
            for his in history:
                if isinstance(his, dict):
                    if his.__contains__("content"):
                        histories.append(
                            {
                                "conversation_id": conversation_id,
                                "is_user": 1 if history[his["from"]] == "user" else 0,
                                "text": history[his["content"]],
                                "text_id": history[his["id"]],
                            }
                        )
        return histories

    def getHistoriesByID(self, conversation_id=None) -> list:
        conversation_id = (
            self.current_conversation if not conversation_id else conversation_id
        )
        if not conversation_id:
            return []
        logging.info(f"Getting histories for {self.email}:{conversation_id}...")
        histories = self._getHistoriesByID(conversation_id)
        if histories is None:
            raise Exception("Something went wrong")
        else:
            return histories

    def getConversations(self) -> dict:
        return self.conversations

    def switchConversation(self, conversation_id: str):
        if not self.conversations.__contains__(conversation_id):
            raise ConversationNotExistError(
                ConversationNotExistError.NotInMap.replace("--id--", conversation_id)
            )
        self.current_conversation = conversation_id


if __name__ == "__main__":
    pass
