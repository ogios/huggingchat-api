from concurrent.futures import Future
from http.cookies import SimpleCookie
from typing import Callable, Dict
import logging
import json
import re

from hugchat_api.core.Chatflow import Chatflow
from hugchat_api.core.CorotineLoop import CorotineLoop
from hugchat_api.core.Message import Message
from hugchat_api.core.Exceptions import ConversationNotExistError
from hugchat_api.core import ListBots
from hugchat_api.core.Customflow import Customflow
from hugchat_api.core.config import RequestData, BASE_URL, BASE_CONVERSATION
from hugchat_api.utils import Request


class Bot:
    def __init__(
        self,
        email: str,
        cookies: SimpleCookie[str],
        loop: CorotineLoop,
        model: str = ListBots.OPENASSISTENT_30B_XOR,
    ):
        self.loop: CorotineLoop = loop
        self.email = email
        self.model = model
        self.cookies = cookies
        self.conversations: Dict[str, str] = dict()
        self.current_conversation = None
        self.fetchConversations()

    def submitAndIfWait(self, func: Callable, wait):
        flow = Customflow.wrap(func)
        fut = self.loop.submit(flow)
        return Customflow.wait(fut) if wait else fut

    def fetchConversations(self, wait: bool = True) -> Future | None:
        """
        Get conversations from html, extracting them using re.
        Support async (by returning a Future).
        """

        # Run func
        async def run():
            logging.info("Fetching all conversations...")
            self.conversations = dict()
            res = await Request.Get(BASE_URL, self.cookies)
            html = await res.text()
            res.close()
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
            return

        # Workflow
        return self.submitAndIfWait(run, wait)

    def chat(
        self,
        text: str,
        conversation_id=None,
        web_search=False,
        max_tries: int = 3,
        custom_data: RequestData | None = None,
    ) -> Message | None:
        """
        Normal chat, send message and wait for reply.
        No Future returns, but Message is keep updating with the conversation.
        """
        conversation_id = (
            self.current_conversation if not conversation_id else conversation_id
        )
        if not conversation_id:
            logging.error("No conversation selected")
            return None
        message = Message(conversation_id, web_search)
        chatflow = Chatflow(
            message,
            text,
            conversation_id,
            self.cookies,
            custom_data=custom_data,
            max_tries=max_tries,
            callback=None
            if self.conversations[conversation_id]
            else [self.updateTitle, [self, conversation_id]],
        )
        self.loop.submit(chatflow)
        return message

    def updateTitle(self, conversation_id: str, wait: bool = True) -> Future | str:
        """
        Get conversation summary
        Support async (by returning a Future).
        """

        # Run func
        async def run():
            if not self.conversations.__contains__(conversation_id):
                raise ConversationNotExistError(
                    ConversationNotExistError.NotInMap.replace(
                        "--id--", conversation_id
                    )
                )
            # request for title
            url = f"{BASE_CONVERSATION}/{conversation_id}/summarize"
            res = await Request.Post(url, cookies=self.cookies)
            if res.status != 200:
                res.close()
                raise Exception("get conversation title failed")
            js = await res.json()
            res.close()

            # set title in map
            self.conversations[conversation_id] = js["title"]
            return js["title"]

        # Workflow
        return self.submitAndIfWait(run, wait)

    def createConversation(self, wait: bool = True) -> Future | str:
        """
        Start a new conversation
        Support async (by returning a Future).
        """

        # Run func
        async def run():
            # Create new empty conversation
            # with model defined
            data = {"model": self.model}
            res = await Request.Post(
                BASE_CONVERSATION, cookies=self.cookies, data=json.dumps(data)
            )
            if res.status != 200:
                res.close()
                raise Exception("create conversation fatal")
            js = await res.json()
            res.close()

            # add conversation id(key) to map
            # and set title to None
            conversation_id = js["conversationId"]
            self.conversations[conversation_id] = None
            self.current_conversation = conversation_id
            return conversation_id

        # Workflow
        return self.submitAndIfWait(run, wait)

    def removeConversation(
        self, conversation_id: str, wait: bool = True
    ) -> Future | None:
        """
        Remove conversation through the index of self.conversations
        Support async (by returning a Future).
        """

        # Run func
        async def run():
            if not self.conversations.__contains__(conversation_id):
                raise ConversationNotExistError(
                    ConversationNotExistError.NotInMap.replace(
                        "--id--", conversation_id
                    )
                )

            # Request for delete
            logging.info(f"Deleting conversation <{conversation_id}>")
            url = f"{BASE_CONVERSATION}/{conversation_id}"
            res = await Request.Delete(url, cookies=self.cookies)
            if res.status != 200:
                logging.info(f"{await res.text()}")
                logging.info("Delete conversation fatal")
                res.close()
                raise Exception("Delete conversation fatal")
            res.close()

            # delete it in map
            del self.conversations[conversation_id]
            if self.current_conversation == conversation_id:
                self.current_conversation = None

        # Workflow
        return self.submitAndIfWait(run, wait)

    async def _getHistoriesByID(self, conversation_id):
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
        url = f"{BASE_CONVERSATION}/{conversation_id}/__data.json?x-sveltekit-invalidated=_1"
        res = await Request.Get(url, cookies=self.cookies)
        if res.status != 200:
            res.close()
            return None

        # Check if histories exists
        data = json.loads(await res.text())
        res.close()
        data = data["nodes"]
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

    def getHistoriesByID(self, conversation_id=None, wait=True) -> Future | list:
        """
        Get one conversation's histories.
        ps: conversation_id can be None (using self.current_conversation).
        Support async (by returning a Future).
        """

        # Run func
        async def run():
            nonlocal conversation_id
            conversation_id = (
                self.current_conversation if not conversation_id else conversation_id
            )
            if not conversation_id:
                return []
            logging.info(f"Getting histories for {self.email}:{conversation_id}...")
            histories = await self._getHistoriesByID(conversation_id)
            if histories is None:
                raise Exception("Something went wrong")
            else:
                return histories

        # Workflow
        return self.submitAndIfWait(run, wait)

    def getConversations(self) -> dict:
        """
        :return:
        {
            id: title
        }
        """
        return self.conversations

    def switchConversation(self, conversation_id: str):
        """
        Change self.current_conversation
        """
        if not self.conversations.__contains__(conversation_id):
            raise ConversationNotExistError(
                ConversationNotExistError.NotInMap.replace("--id--", conversation_id)
            )
        self.current_conversation = conversation_id


if __name__ == "__main__":
    pass
