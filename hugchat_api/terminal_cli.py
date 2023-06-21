import gc, os, argparse, time
import getpass
import logging
import traceback
from rich.console import Console
from rich.markdown import Markdown

from .core import HuggingChat
from .core.Message import Message
from .core.Sign import Sign
from .core.Bot import Bot
from .utils import color, formatHistory, formatConversations, getTextFromInput

COOKIE_DIR_PATH = os.path.abspath(os.path.dirname(__file__)) + "/usercookies"
CONSOLE = Console()
hug = HuggingChat()

# FLAG = False
WEB_SEARCH = False
NEW_CONVERSATION = False

logging.getLogger().setLevel(logging.INFO)

def checkCookies(u):
    login = Sign(u, None)
    try:
        login.loadCookiesFromDir(COOKIE_DIR_PATH)
        return True
    except Exception as e:
        # print(e)
        return False


def login(u, p=None, force=False):
    if not p:
        logging.info(f"No Password input, trying to load it from mysql or files")
        login = Sign(u, p)
        cookies = login.loadCookiesFromDir(COOKIE_DIR_PATH)
    else:
        login = Sign(u, p)
        if force:
            cookies = login.login(save=True, cookie_dir_path=COOKIE_DIR_PATH)
        else:
            try:
                cookies = login.loadCookiesFromDir(COOKIE_DIR_PATH)
            except:
                cookies = login.login(save=True, cookie_dir_path=COOKIE_DIR_PATH)
    return cookies


def updateMSG(message: Message):
    # global FLAG
    while not message.done:
        if message.error:
            logging.error(str(message.error))
            return
        time.sleep(0.5)
        
    msg = message.getFinalText()
    string = f"({color('Open-Assistant', 'blue')}): {msg}"
    try:
        markdown = Markdown(string)
        CONSOLE.print(markdown)
    except:
        print(string)


def updateWebSearch(message: Message):
    if not message.web_search_enabled:
        return
    message.getWebSearchSteps()
    pass
    # if js["type"] == "web_search" and js.__contains__("data"):
    #     data: dict = js["data"]
    #     if data["type"] == "update" and data.__contains__("message"):
    #         string = f"* {data['message']}{' - ' + str(data['args']) if data.__contains__('args') else ''}"
    #         print(string)
    #     elif data["type"] == "result":
    #         print(f"* result - {data['id']}")
    #     else:
    #         logging.error(f"Wrong step: {js}")
    # else:
    #     logging.error(f"Wrong step: {js}")


def changeWeb_search():
    global WEB_SEARCH
    WEB_SEARCH = True if not WEB_SEARCH else False
    print(f"WEB_SEARCH is set to `{WEB_SEARCH}`")


def main(EMAIL, PASSWD):
    # global FLAG
    global WEB_SEARCH
    global NEW_CONVERSATION
    
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-u",
        type=str,
        help="登录邮箱(没账号请先注册一个) - email to be sign in.(sign up before this)"
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
    openassistant: Bot = hug.getBot(u, cookies=cookies)
    gc.collect()
    while 1:
        try:
            gc.collect()
            # while FLAG:
            #     time.sleep(0.1)
            #     continue
            text = getTextFromInput(openassistant.current_conversation)
            command = text.strip()
            if command[0] == "/":
                command = command[1:].split(" ")
                if command[0] == "exit" or command[0] == "q":
                    os._exit(0)
                elif command[0] == "new":
                    openassistant.createConversation()
                    NEW_CONVERSATION = True
                elif command[0] == "ls":
                    print(formatConversations(openassistant.getConversations()))
                elif command[0] == "cd":
                    try:
                        openassistant.switchConversation(int(command[1]))
                    except:
                        print("cd fatal")
                elif command[0] == "rm":
                    try:
                        openassistant.removeConversation(int(command[1]))
                    except Exception as e:
                        
                        print(f"remove conversation fatal: {e}")
                elif command[0] == "old":
                    print(formatHistory(openassistant.getHistoriesByID()))
                elif command[0] == "web":
                    changeWeb_search()
                elif command[0] == "reload":
                    print("Reloading conversations...")
                    openassistant.fetchConversations()
                    for i in openassistant.conversations:
                        openassistant.updateTitle(i['id'])
                    print("done.")
                    print(formatConversations(openassistant.getConversations()))
                else:
                    print("wrong command。")
                    continue
            else:
                if not openassistant.current_conversation:
                    print(
                        "Please select or create a conversation using '/ls' and '/cd <int>' or '/new'.")
                    continue
                
                message = openassistant.chat(
                    text,
                    web=WEB_SEARCH,
                    callback=(openassistant.updateTitle, (openassistant.current_conversation,)) if NEW_CONVERSATION else None
                )
                updateWebSearch(message)
                updateMSG(message)
                # FLAG = True
        except Exception as e:
            traceback.print_exc()


if __name__ == "__main__":
    EMAIL = ""
    PASSWD = ""
    main(EMAIL, PASSWD)
