from http.cookies import SimpleCookie

from hugchat_api.core.CorotineLoop import CorotineLoop
from .Bot import Bot
from .Sign import Sign
from . import ListBots


class HuggingChat:
    def __init__(self, *args):
        self.loop = CorotineLoop()

    def getBot(
        self,
        email: str,
        cookies: SimpleCookie[str],
        model: str = ListBots.OPENASSISTENT_30B_XOR,
    ):
        bot = Bot(
            email=email,
            cookies=cookies,
            model=model,
            loop=self.loop,
        )
        return bot

    def getSign(self, email, passwd):
        return Sign(
            email=email,
            passwd=passwd,
            loop=self.loop,
        )
