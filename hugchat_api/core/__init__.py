from requests.sessions import RequestsCookieJar


from .Bot import Bot
from .Sign import Sign
from .ThreadPool import ThreadPool
from . import ListBots


class HuggingChat:
    def __init__(self, max_thread: int = 5):
        # self.thread_pool = ThreadPoolExecutor(max_workers=max_thread)
        self.thread_pool = ThreadPool(max_thread)
    
    def getBot(self, email: str, cookies: RequestsCookieJar, model: str = ListBots.OPENASSISTENT_30B_XOR):
        bot = Bot(
            email=email,
            cookies=cookies,
            thread_pool=self.thread_pool,
            model=model,
        )
        return bot
    
    def getSign(self, email, passwd):
        return Sign(
            email=email,
            passwd=passwd
        )
