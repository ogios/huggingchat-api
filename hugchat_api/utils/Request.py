from http.cookies import SimpleCookie
from aiohttp import ClientResponse
import aiohttp

_headers = {
    "Referer": "https://huggingface.co/chat",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36 Edg/112.0.1722.64",
}

_session = None

async def init(loop):
    global _session
    _session = aiohttp.ClientSession(trust_env=True, loop=loop)


async def Get(
    url: str,
    cookies: SimpleCookie[str],
    headers=None,
    params=None,
    allow_redirects=True,
) -> ClientResponse:
    """
    Requests GET
    """
    res = await _session.get(
        url,
        params=params,
        headers=_headers if not headers else headers,
        cookies=cookies,
        allow_redirects=allow_redirects,
    )
    return res


async def Post(
    url: str,
    cookies: SimpleCookie[str],
    headers=None,
    params=None,
    data=None,
    allow_redirects=True,
) -> ClientResponse:
    """
    Requests POST
    """
    res = await _session.post(
        url,
        params=params,
        data=data,
        headers=_headers if not headers else headers,
        cookies=cookies,
        allow_redirects=allow_redirects,
    )
    return res


async def Delete(
    url: str, cookies: SimpleCookie[str], headers: dict = {}
) -> ClientResponse:
    res = await _session.delete(
        url,
        headers=_headers if not headers else headers,
        cookies=cookies,
    )
    return res
