import datetime
from typing import List


def color(string, color: str) -> str:
    dic = {
        'white': '\033[30m',
        'red': '\033[31m',
        'green': '\033[32m',
        'yellow': '\033[33m',
        'blue': '\033[34m',
        'purple': '\033[35m',
        'cyan': '\033[36m',
        'black': '\033[37m'
    }
    return dic[color] + string + '\033[0m'


def dictToString(cookies: dict) -> str:
    cookie = ""
    for i in cookies:
        cookie += f"{i}={cookies[i]}; "
    return cookie


def formatHistory(histories: List[dict]) -> str:
    string = f"\n====== Histories of <{histories[0]['conversation_id'] if len(histories) > 1 else ''}> ======\n"
    for i in histories:
        string += f"({color('user', 'green') if i['is_user'] else color('Open-Assistant', 'blue')}): {i['text']}\n"
    string += "\n"
    return string


def getTextFromInput(conversation_id, addition: str = ""):
    while 1:
        text = input(f"{addition}({conversation_id}) > ")
        if not text:
            continue
        else:
            return text
        

def formatConversations(conversations: List[dict]):
    string = "* Conversations established:\n\n"
    for i in range(len(conversations)):
        string += f"	{i}. {conversations[i]['title']}\n"
    # string += "\n"
    return string


def getTime():
    return str(datetime.datetime.now())


