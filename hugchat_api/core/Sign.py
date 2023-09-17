from http.cookies import SimpleCookie
import logging
import os
import re
import json
import time

from aiohttp import ClientResponse
from hugchat_api.core.Workflow import Workflow
from hugchat_api.core.Customflow import Customflow
from hugchat_api.utils import Request
from .CorotineLoop import CorotineLoop


class Sign(Workflow):
    def __init__(
        self,
        email: str,
        loop: CorotineLoop,
        passwd: str | None = None,
    ) -> None:
        self.loop = loop
        self.email: str = email
        self.passwd: str | None = passwd
        self.headers = {
            "Referer": "https://huggingface.co/",
            # "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36 Edg/112.0.1722.64",
        }
        self.cookies: SimpleCookie[str] = SimpleCookie()

        # cookie dir and file
        self.DEFAULT_PATH_DIR = (
            os.path.dirname(os.path.abspath(__file__)) + "/usercookies"
        )
        self.DEFAULT_COOKIE_PATH = self.DEFAULT_PATH_DIR + f"/{email}.json"

    async def _requestsGet(
        self, url: str, params=None, allow_redirects=True
    ) -> ClientResponse:
        res = await Request.Get(
            url,
            params=params,
            headers=self.headers,
            cookies=self.cookies,
            # proxies=self.proxies,
            allow_redirects=allow_redirects,
        )
        self._refreshCookies(res.cookies)
        return res

    async def _requestsPost(
        self,
        url: str,
        headers=None,
        params=None,
        data=None,
        allow_redirects=True,
    ) -> ClientResponse:
        res = await Request.Post(
            url,
            params=params,
            data=data,
            headers=self.headers if headers is None else headers,
            cookies=self.cookies,
            allow_redirects=allow_redirects,
        )
        self._refreshCookies(res.cookies)
        return res

    def _refreshCookies(self, cookies: SimpleCookie[str]):
        self.cookies.update(cookies)

    async def _SigninWithEmail(self):
        url = "https://huggingface.co/login"
        data = {
            "username": self.email,
            "password": self.passwd,
        }
        res = await self._requestsPost(url=url, data=data, allow_redirects=False)
        if res.status == 400:
            res.close()
            raise Exception("Incorrect username or password")

    async def _getAuthURL(self) -> str:
        url = "https://huggingface.co/chat/login"
        headers = {
            "Referer": "https://huggingface.co/chat/login",
            "User-Agent": self.headers["User-Agent"],
            "Content-Type": "application/x-www-form-urlencoded",
        }
        res = await self._requestsPost(url, headers=headers, allow_redirects=False)
        if res.status == 200:
            # location = res.headers.get("Location", None)
            # js = await res.json()
            data = json.loads(await res.text())
            location = data["location"]
            res.close()
            if location:
                return location
            else:
                raise Exception("No authorize url!")
        else:
            res.close()
            raise Exception("Something went wrong!")

    async def _grantAuth(self, url: str) -> int:
        res = await self._requestsGet(url, allow_redirects=False)
        if res.headers.__contains__("location"):
            location = res.headers["location"]
            res = await self._requestsGet(location, allow_redirects=False)
            if res.cookies.__contains__("hf-chat"):
                res.close()
                return 1
        # raise Exception("grantAuth fatal")
        if res.status != 200:
            raise Exception("grant auth fatal!")
        csrf = re.findall(
            '/oauth/authorize.*?name="csrf" value="(.*?)"', await res.text()
        )
        if len(csrf) == 0:
            raise Exception("No csrf found!")
        data = {"csrf": csrf[0]}
        res.close()

        res = await self._requestsPost(url, data=data, allow_redirects=False)
        if res.status != 303:
            raise Exception(f"get hf-chat cookies fatal! - {res.status}")
        else:
            location = res.headers.get("Location")
        res.close()
        res = await self._requestsGet(location, allow_redirects=False)
        if res.status != 302:
            res.close()
            raise Exception(f"get hf-chat cookie fatal! - {res.status}")
        else:
            res.close()
            return 1

    def saveCookiesToDir(self, cookie_dir_path: str | None = None) -> str:

        # path
        cookie_dir_path = (
            self.DEFAULT_PATH_DIR if not cookie_dir_path else cookie_dir_path
        )
        if not cookie_dir_path.endswith("/"):
            cookie_dir_path += "/"
        cookie_path = cookie_dir_path + f"{self.email}.json"
        if not os.path.exists(cookie_dir_path):
            logging.info("Cookie directory not exist, creating...")
            os.makedirs(cookie_dir_path)
        logging.info(f"Cookie store path: {cookie_path}")

        # save
        d = {}
        for cookie in self.cookies.items():
            d[cookie[0]] = cookie[1].value
        with open(cookie_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(d))
        return cookie_path

    def _getCookiePath(self, cookie_dir_path: str) -> str:
        if not cookie_dir_path.endswith("/"):
            cookie_dir_path += "/"
        if not os.path.exists(cookie_dir_path):
            return ""
        files = os.listdir(cookie_dir_path)
        for i in files:
            if i == f"{self.email}.json":
                return cookie_dir_path + i
        return ""

    def loadCookiesFromDir(
        self, cookie_dir_path: str | None = None
    ) -> SimpleCookie[str]:
        
        # path
        cookie_dir_path = (
            self.DEFAULT_PATH_DIR if not cookie_dir_path else cookie_dir_path
        )
        cookie_path = self._getCookiePath(cookie_dir_path)
        if not cookie_path:
            raise Exception(
                f"Cookie not found. please check the path given: {cookie_dir_path}.\n"
                + f"Cookie file must be named like this: 'your_email'+'.json': '{self.email}.json'"
            )

        #load
        with open(cookie_path, "r", encoding="utf-8") as f:
            try:
                js = json.loads(f.read())
                self.cookies.load(js)
                return self.cookies
            except Exception:
                raise Exception(
                    "load cookies from files fatal. Please check the format"
                )

    async def run(self):
        await self._SigninWithEmail()
        location = await self._getAuthURL()
        if await self._grantAuth(location):
            pass
        if self.save:
            self.saveCookiesToDir(self.cookie_dir_path)
        return self.cookies

    def login(
        self, save: bool = False, cookie_dir_path: str | None = None
    ) -> SimpleCookie[str]:
        self.save = save
        self.cookie_dir_path = cookie_dir_path
        fut = self.loop.submit(self)
        return Customflow.wait(fut)


if __name__ == "__main__":
    email = os.getenv("EMAIL")
    passwd = os.getenv("PASSWD")
    sign = Sign(email, passwd)
    cookies = sign.login()
    sign.saveCookiesToDir()
    print(cookies)
