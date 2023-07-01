import logging
import os
# import re
import requests

import requests.utils
import requests.sessions
import json


class Sign:
    def __init__(self, email: str, passwd: str = None) -> None:
        self.email: str = email
        self.passwd: str = passwd
        self.headers = {
            "Referer": "https://huggingface.co/",
            # "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36 Edg/112.0.1722.64",
        }
        self.cookies = requests.sessions.RequestsCookieJar()
        
        self.DEFAULT_PATH_DIR = os.path.dirname(os.path.abspath(__file__)) + "/usercookies"
        self.DEFAULT_COOKIE_PATH = self.DEFAULT_PATH_DIR + f"/{email}.json"
        # self.COOKIE_DIR = os.path.dirname(os.path.abspath(__file__)) + "/usercookies"
        # self.COOKIE_PATH = self.COOKIE_DIR + f"/{self.email}.json"
        # if not os.path.exists(self.COOKIE_DIR):
        #     logging.info("Cookie directory not found, creating...")
        #     os.makedirs(self.COOKIE_DIR)
        # logging.info(f"Cookie store path: {self.COOKIE_PATH}")
    
    def _requestsGet(self, url: str, params=None, allow_redirects=True) -> requests.Response:
        res = requests.get(
            url,
            params=params,
            headers=self.headers,
            cookies=self.cookies,
            # proxies=self.proxies,
            allow_redirects=allow_redirects,
        )
        self._refreshCookies(res.cookies)
        return res
    
    def _requestsPost(self, url: str, headers=None, params=None, data=None, stream=False,
                      allow_redirects=True) -> requests.Response:
        res = requests.post(
            url,
            stream=stream,
            params=params,
            data=data,
            headers=self.headers if headers == None else headers,
            cookies=self.cookies,
            allow_redirects=allow_redirects
        )
        self._refreshCookies(res.cookies)
        return res
    
    def _refreshCookies(self, cookies: requests.sessions.RequestsCookieJar):
        dic = cookies.get_dict()
        for i in dic:
            self.cookies.set(i, dic[i])
    
    def _SigninWithEmail(self):
        url = "https://huggingface.co/login"
        data = {
            "username": self.email,
            "password": self.passwd,
        }
        res = self._requestsPost(url=url, data=data, allow_redirects=False)
        if res.status_code == 400:
            raise Exception("Incorrect username or password")
    
    def _getAuthURL(self) -> str:
        url = "https://huggingface.co/chat/login"
        headers = {
            "Referer": "https://huggingface.co/chat/login",
            "User-Agent": self.headers["User-Agent"],
            "Content-Type": "application/x-www-form-urlencoded"
        }
        res = self._requestsPost(url, headers=headers, allow_redirects=False)
        if res.status_code == 200:
            # location = res.headers.get("Location", None)
            location = res.json()["location"]
            if location:
                return location
            else:
                raise Exception("No authorize url!")
        else:
            raise Exception("Something went wrong!")
    
    def _grantAuth(self, url: str) -> int:
        res = self._requestsGet(url, allow_redirects=False)
        if res.headers.__contains__("location"):
            location = res.headers["location"]
            res = self._requestsGet(location, allow_redirects=False)
            if res.cookies.__contains__("hf-chat"):
                return 1
        raise Exception("grantAuth fatal")
        # if res.status_code != 200:
        #     raise Exception("grant auth fatal!")
        # csrf = re.findall('/oauth/authorize.*?name="csrf" value="(.*?)"', res.text)
        # if len(csrf) == 0:
        #     raise Exception("No csrf found!")
        # data = {
        #     "csrf": csrf[0]
        # }
        #
        # res = self._requestsPost(url, data=data, allow_redirects=False)
        # if res.status_code != 303:
        #     raise Exception(f"get hf-chat cookies fatal! - {res.status_code}")
        # else:
        #     location = res.headers.get("Location")
        # res = self._requestsGet(location, allow_redirects=False)
        # if res.status_code != 302:
        #     raise Exception(f"get hf-chat cookie fatal! - {res.status_code}")
        # else:
        #     return 1
    
    def saveCookiesToDir(self, cookie_dir_path: str = None) -> str:
        cookie_dir_path = self.DEFAULT_PATH_DIR if not cookie_dir_path else cookie_dir_path
        if not cookie_dir_path.endswith("/"):
            cookie_dir_path += "/"
        cookie_path = cookie_dir_path + f"{self.email}.json"
        if not os.path.exists(cookie_dir_path):
            logging.info("Cookie directory not exist, creating...")
            os.makedirs(cookie_dir_path)
        logging.info(f"Cookie store path: {cookie_path}")
        
        with open(cookie_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(self.cookies.get_dict()))
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
    
    def loadCookiesFromDir(self, cookie_dir_path: str = None) -> requests.sessions.RequestsCookieJar:
        cookie_dir_path = self.DEFAULT_PATH_DIR if not cookie_dir_path else cookie_dir_path
        cookie_path = self._getCookiePath(cookie_dir_path)
        if not cookie_path:
            raise Exception(f"Cookie not found. please check the path given: {cookie_dir_path}.\n" +
                            f"Cookie file must be named like this: 'your_email'+'.json': '{self.email}.json'")
        
        with open(cookie_path, "r", encoding="utf-8") as f:
            try:
                js = json.loads(f.read())
                for i in js.keys():
                    self.cookies.set(i, js[i])
                    logging.info(f"{i} loaded")
                return self.cookies
            except:
                raise Exception("load cookies from files fatal. Please check the format")
    
    def login(self, save: bool = False, cookie_dir_path: str = None) -> requests.sessions.RequestsCookieJar:
        self._SigninWithEmail()
        location = self._getAuthURL()
        if self._grantAuth(location):
            pass
        if save:
            self.saveCookiesToDir(cookie_dir_path)
        return self.cookies


if __name__ == "__main__":
    email = os.getenv("EMAIL")
    passwd = os.getenv("PASSWD")
    sign = Sign(email, passwd)
    cookies = sign.login()
    sign.saveCookiesToDir()
    print(cookies)
