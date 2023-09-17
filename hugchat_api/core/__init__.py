from http.cookies import SimpleCookie
import asyncio

from hugchat_api.core.CorotineLoop import CorotineLoop
from .Bot import Bot
from .Sign import Sign
from . import ListBots
from hugchat_api.utils import Request


class HuggingChat:
    def __init__(self, *args):
        self.loop = CorotineLoop()
        asyncio.run(Request.init(self.loop.loop))

    def getBot(
        self,
        email: str,
        cookies: SimpleCookie[str],
        model: str = ListBots.OPENASSISTENT_30B_XOR,
    ) -> Bot:
        bot = Bot(
            email=email,
            cookies=cookies,
            model=model,
            loop=self.loop,
        )
        return bot

    def getSign(self, email, passwd = None) -> Sign:
        return Sign(
            email=email,
            passwd=passwd,
            loop=self.loop,
        )
