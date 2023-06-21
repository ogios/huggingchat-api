from concurrent.futures import ThreadPoolExecutor
from requests.sessions import RequestsCookieJar
from requests import sessions

from .Bot import Bot
from .Sign import Sign
from .ThreadPool import ThreadPool


class HuggingChat:
    def __init__(self, max_thread: int = 5):
        # self.thread_pool = ThreadPoolExecutor(max_workers=max_thread)
        self.thread_pool = ThreadPool(max_thread)
    
    def getBot(self, email: str, cookies: RequestsCookieJar):
        bot = Bot(
            email=email,
            cookies=cookies,
            thread_pool=self.thread_pool
        )
        return bot
    
    def getSign(self, email, passwd):
        return Sign(
            email=email,
            passwd=passwd
        )
