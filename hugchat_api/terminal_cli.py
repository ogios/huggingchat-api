import gc, os, argparse, time
import getpass
import logging
import traceback
import asyncio
import typing
# from rich.console import Console
# from rich.markdown import Markdown

from .core import HuggingChat
from .core.Message import Message
from .core.Sign import Sign
from .core.Bot import Bot
from .utils import color, formatHistory, formatConversations, getTextFromInput, getIdByIndex
from .core import ListBots

# COOKIE_DIR_PATH = os.path.abspath(os.path.dirname(__file__)) + "/usercookies"
# CONSOLE = Console()
hug = HuggingChat()

# FLAG = False
WEB_SEARCH = False
NEW_CONVERSATION = False

logging.getLogger().setLevel(logging.INFO)

def checkCookies(u):
    login = Sign(u, None)
    try:
        login.loadCookiesFromDir()
        return True
    except Exception as e:
        # print(e)
        return False


def login(u, p=None, force=False):
    if not p:
        logging.info(f"No Password input, trying to load it from mysql or files")
        login = Sign(u, p)
        cookies = login.loadCookiesFromDir()
    else:
        login = Sign(u, p)
        if force:
            cookies = login.login(save=True)
        else:
            try:
                cookies = login.loadCookiesFromDir()
            except:
                cookies = login.login(save=True)
    return cookies


# def updateMSG(message: Message):
#     # global FLAG
#     while not message.done:
#         if message.error:
#             logging.error(str(message.error))
#             return
#         time.sleep(0.5)
#         
#     msg = message.getFinalText()
#     string = f"({color('HFBot: ', 'blue')}): {msg}"
#     print(string)
#     # try:
#     #     markdown = Markdown(string)
#     #     CONSOLE.print(markdown)
#     # except:
#     #     print(string)
#
#
# def updateWebSearch(message: Message):
#     if not message.web_search_enabled:
#         return
#     # length = 0
#     while not message.web_search_done:
#         # c = message.getWebSearchSteps()
#         # if len(c) > length:
#         #     for i in c[length-1:]:
#         #         print(i)
#         #         length += 1
#         time.sleep(0.5)
#     # print("======")
#     # print("======")
#     print(message.web_search_steps)
#     # if js["type"] == "web_search" and js.__contains__("data"):
#     #     data: dict = js["data"]
#     #     if data["type"] == "update" and data.__contains__("message"):
#     #         string = f"* {data['message']}{' - ' + str(data['args']) if data.__contains__('args') else ''}"
#     #         print(string)
#     #     elif data["type"] == "result":
#     #         print(f"* result - {data['id']}")
#     #     else:
#     #         logging.error(f"Wrong step: {js}")
#     # else:
#     #     logging.error(f"Wrong step: {js}")

class Notice:
    _notice: int = 0
    async def waitForAccept(self):
        while self._notice:
            await asyncio.sleep(0.1)
    def notice(self):
        self._notice = 1
    def accept(self) -> int:
        if self._notice:
            self._notice = 0
            return 1
        else:
            return 0
            

async def wait(message: Message, lock: Notice):
    if message.web_search_enabled:
        while not message.web_search_done:
            await asyncio.sleep(0.01)
        else:
            lock.notice()
            await lock.waitForAccept()
            print(f"\r{message.web_search_steps}", flush=True)
    while not message.isDone():
        await asyncio.sleep(0.01)
    else:
        lock.notice()
        await lock.waitForAccept()
        msg = message.getFinalText()
        string = f"\r({color('HFBot', 'blue')}): {msg}"
        print(string, flush=True)



def printWait() -> typing.Callable:
    tick = time.time()
    index = 0
    count = 3
    def c():
        nonlocal tick, index
        if time.time() - tick >= 0.5:
            tick = time.time()
            content = ["."] * count
            content[index] = "·"
            index = (index + 1) % count
            print(f"\r{''.join(content)}", flush=True, end="")
    return c
    

async def waitAndPrint(message: Message, lock: Notice):
    print_wait = printWait()
    if message.web_search_enabled:
        while True:
            if lock.accept():
                break
            print_wait()
            await asyncio.sleep(0.01)
    while True:
        if lock.accept():
            break
        print_wait()
        await asyncio.sleep(0.01)




def changeWeb_search():
    global WEB_SEARCH
    WEB_SEARCH = True if not WEB_SEARCH else False
    print(f"WEB_SEARCH is set to `{WEB_SEARCH}`")


async def main(EMAIL: str, PASSWD: str, loop: asyncio.AbstractEventLoop):
    # global FLAG
    global WEB_SEARCH
    global NEW_CONVERSATION
    
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-u",
        type=str,
        help="email to be sign in.(sign up before this)"
    )
    parser.add_argument(
        "-p",
        action="store_true",
        help="再终端中输入密码(每账号请先注册一个) - input password in terminal(sign up before this)"
    )
    parser.add_argument(
        "-f",
        action="store_true",
        help="忽视已保存信息强制登录 - ignore the stored cookies and login"
    )
    args = parser.parse_args()
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
    bot: Bot.Bot = hug.getBot(u, cookies=cookies, model=ListBots.FALCON_180B)
    gc.collect()
    while 1:
        try:
            gc.collect()
            # while FLAG:
            #     time.sleep(0.1)
            #     continue
            text = getTextFromInput(bot.current_conversation)
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
                        bot.updateTitle(i['id'])
                    print("done.")
                    print(formatConversations(bot.getConversations()))
                else:
                    print("wrong command。")
                    continue
            else:
                if not bot.current_conversation:
                    print(
                        "Please select or create a conversation using '/ls' and '/cd <int>' or '/new'.")
                    continue
                
                message = bot.chat(
                    text,
                    conversation_id=bot.current_conversation,
                    web_search=WEB_SEARCH,
                    # callback=(bot.updateTitle, (bot.current_conversation,)) if NEW_CONVERSATION else None
                )
                lock = Notice()
                loop.create_task(waitAndPrint(message, lock))
                await wait(message, lock)
                # updateWebSearch(message)
                # updateMSG(message)
                # FLAG = True
        except Exception:
            traceback.print_exc()


if __name__ == "__main__":
    EMAIL = os.getenv("EMAIL")
    PASSWD = os.getenv("PASSWD")
    event_loop = asyncio.get_event_loop()
    try:
        event_loop.run_until_complete(main(EMAIL, PASSWD, event_loop))
    except Exception:
        traceback.print_exc()
        event_loop.close()
