import requests
from requests.sessions import RequestsCookieJar
from urllib3.util import retry

_headers = {
    "Referer": "https://huggingface.co/chat",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36 Edg/112.0.1722.64",
}


def Get(
    url: str, cookies: RequestsCookieJar, params=None, stream=False
) -> requests.Response:
    """
    Requests GET
    """
    res = requests.get(
        url,
        params=params,
        headers=_headers,
        cookies=cookies,
        stream=stream,
        # verify=False,
    )
    return res


def Post(
    url: str,
    cookies: RequestsCookieJar,
    headers=None,
    params=None,
    data=None,
    stream=False,
) -> requests.Response:
    """
    Requests POST
    """
    res = requests.post(
        url,
        stream=stream,
        params=params,
        data=data,
        headers=_headers if not headers else headers,
        cookies=cookies,
        # verify=False,
    )
    return res


def Delete(
    url: str, cookies: RequestsCookieJar, headers: dict = {}
) -> requests.Response:
    res = requests.delete(
        url,
        headers=_headers if not headers else headers,
        cookies=cookies,
    )
    return res
