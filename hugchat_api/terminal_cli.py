import gc, os, argparse
import getpass
import logging
import traceback
import asyncio
import time
import typing

from hugchat_api.utils.PrintWeb import PrintWeb

from .utils.PrintLoop import PrintLoop


from .core import HuggingChat
from .core.Message import Message
from .core.Sign import Sign
from .core.Bot import Bot
from .utils import (
    color,
    formatHistory,
    formatConversations,
    getTextFromInput,
    getIdByIndex,
)
from .core import ListBots

# COOKIE_DIR_PATH = os.path.abspath(os.path.dirname(__file__)) + "/usercookies"
# CONSOLE = Console()
hug = HuggingChat()

# FLAG = False
WEB_SEARCH = False
NEW_CONVERSATION = False


def checkCookies(u):
    login = Sign(u, None)
    try:
        login.loadCookiesFromDir()
        return True
    except Exception:
        # print(e)
        return False


def login(u, p=None, force=False):
    if not p:
        logging.info("No Password input, trying to load it from mysql or files")
        login = Sign(u, p)
        cookies = login.loadCookiesFromDir()
    else:
        login = Sign(u, p)
        if force:
            cookies = login.login(save=True)
        else:
            try:
                cookies = login.loadCookiesFromDir()
            except Exception:
                cookies = login.login(save=True)
    return cookies


# def printWait() -> typing.Callable:
#     tick = time.time()
#     index = 0
#     count = 3
#     dots = "·.."
#
#     def c() -> str:
#         nonlocal tick, index, dots
#         if time.time() - tick >= 0.5:
#             tick = time.time()
#             content = ["."] * count
#             content[index] = "·"
#             index = (index + 1) % count
#             dots = "".join(content)
#             # print(f"\r{dots}", flush=True, end="")
#         return dots
#
#     return c


# async def waitAndPrint(message: Message):
#     print_wait = printWait()
#     if message.web_search_enabled:
#         while not message.web_search_done:
#             print_wait()
#             await asyncio.sleep(0.01)
#         print(f"\r{message.web_search_steps}", flush=True)
#     while not message.isDone():
#         if message.error is not None:
#             raise message.error
#         content = "\r" + "".join(message.getText())
#         content += print_wait()
#         print(content, flush=True, end="")
#         await asyncio.sleep(0.01)
#     else:
#         content = "".join(message.getText())
#         string = f"\r({color('HFBot', 'blue')}): {content}"
#         print(string, flush=True)
#     return


def printloop(message: Message):
    printweb = PrintWeb(message)
    printweb.update()
    print()
    loop = PrintLoop(message)
    string = f"\r({color('HFBot', 'blue')}): "
    print(string)
    loop.main()
    print()
    printweb.sources()
    print()


def changeWeb_search():
    global WEB_SEARCH
    WEB_SEARCH = True if not WEB_SEARCH else False
    print(f"WEB_SEARCH is set to `{WEB_SEARCH}`")


async def main(EMAIL: str, PASSWD: str | None):
    # global FLAG
    global WEB_SEARCH
    global NEW_CONVERSATION

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-u", type=str, help="email to be sign in.(sign up before this)"
    )
    parser.add_argument(
        "-p",
        action="store_true",
        help="再终端中输入密码(每账号请先注册一个) - input password in terminal(sign up before this)",
    )
    parser.add_argument(
        "-f",
        action="store_true",
        help="忽视已保存信息强制登录 - ignore the stored cookies and login",
    )
    parser.add_argument("--debug", action="store_true", default=False)
    args = parser.parse_args()
    level = logging.DEBUG if args.debug else logging.WARNING
    logging.basicConfig(
        format="%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s",
        encoding="utf-8",
        level=level,
        filename="terminal_cli.log",
        filemode="w",
    )
    force = args.f
    u = EMAIL if not args.u else args.u
    print(f"Login in as <{u}>")
    if args.p:
        p = getpass.getpass()
    elif not checkCookies(u):
        p = getpass.getpass() if not PASSWD else PASSWD
    else:
        p = None

    cookies = login(u, p, force)
    print(f"You are now logged in as <{u}>")
    bot: Bot = hug.getBot(u, cookies=cookies, model=ListBots.FALCON_180B)
    gc.collect()
    while 1:
        try:
            gc.collect()
            text = getTextFromInput(bot.current_conversation)
            if text is None:
                continue
            command = text.strip()
            if command[0] == "/":
                command = command[1:].split(" ")
                if command[0] == "exit" or command[0] == "q":
                    os._exit(0)
                elif command[0] == "new":
                    bot.createConversation()
                    NEW_CONVERSATION = True
                elif command[0] == "ls":
                    print(formatConversations(bot.getConversations()))
                elif command[0] == "cd":
                    try:
                        tmp_id = getIdByIndex(bot.conversations, int(command[1]))
                        bot.switchConversation(tmp_id)
                    except Exception:
                        print("cd fatal")
                elif command[0] == "rm":
                    try:
                        tmp_id = getIdByIndex(bot.conversations, int(command[1]))
                        bot.removeConversation(tmp_id)
                    except Exception as e:
                        print(f"remove conversation fatal: {e}")
                elif command[0] == "old":
                    print(formatHistory(bot.getHistoriesByID()))
                elif command[0] == "web":
                    changeWeb_search()
                elif command[0] == "reload":
                    print("Reloading conversations...")
                    bot.fetchConversations()
                    for i in bot.conversations:
                        bot.updateTitle(i["id"])
                    print("done.")
                    print(formatConversations(bot.getConversations()))
                else:
                    print("wrong command。")
                    continue
            else:
                if not bot.current_conversation:
                    print(
                        "Please select or create a conversation using '/ls' and '/cd <int>' or '/new'."
                    )
                    continue

                message = bot.chat(
                    text,
                    conversation_id=bot.current_conversation,
                    web_search=WEB_SEARCH,
                )
                if message is None:
                    continue
                # await waitAndPrint(message)
                printloop(message)
        except Exception:
            traceback.print_exc()


if __name__ == "__main__":
    EMAIL = os.getenv("EMAIL")
    if not EMAIL:
        print("please provide email")
        os._exit(0)
    PASSWD = os.getenv("PASSWD")
    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)
    try:
        event_loop.run_until_complete(main(EMAIL, PASSWD))
    except Exception:
        traceback.print_exc()
        event_loop.close()
