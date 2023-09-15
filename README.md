# Huggingchat api

**You Star You Win A BILLION$$$(maybe,it's not impossible that it would happen)**

> This is my first pypi project. Experienced some annoying moments, but i managed to do it anyway

[![PyPI version](https://img.shields.io/pypi/v/hugchat-api.svg)](https://pypi.python.org/pypi/hugchat-api/)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/hugchat-api.svg)](https://pypi.python.org/pypi/hugchat-api/)

[![Downloads](https://static.pepy.tech/badge/hugchat-api)](https://pepy.tech/project/hugchat-api)

```shell
pip install hugchat-api
```

## Sign in
```python
import os
from hugchat_api import HuggingChat

EMAIL = os.getenv("EMAIL_QQ")
PASSWD = ""
COOKIE_STORE_PATH = "./usercookies"

# create ThreadPool
HUG = HuggingChat(max_thread=1)       

# initialize sign in funciton
sign = HUG.getSign(EMAIL, PASSWD)   
# sign in or...
cookies = sign.login(save=True, cookie_dir_path=COOKIE_STORE_PATH)
# load it from a specified directory
cookies = sign.loadCookiesFromDir(cookie_dir_path=COOKIE_STORE_PATH)
```

<details>

<summary>

## API Usage

</summary>


- Create Bot
```python
bot = HUG.getBot(email=EMAIL, cookies=cookies, model=ListBots.<model_name>)
```
- Get all conversations & Print title
```python
conversations = bot.getConversations()
conv_id = list(conversations.keys())[0]
print(conversations[conv_id])
```
- Get all chat histories by conversation_id
```python
histories = bot.getHistoriesByID(conversation_id=conv_id)
print(formatHistory(histories))
```
- Delete a conversation
```python
bot.removeConversation(conversation_id=conv_id)
```
- Create a new conversation
```python
conversation_id = bot.createConversation()
```
- Chat
```python
# chat
message = bot.chat(
    text="hi",
    conversation_id=conversation_id,
    web_search=True,
    max_tries=2,
    # callback=(bot.updateTitle, (conversation_id,))
)
# wait the full text or...
while not message.web_search_done:
    time.sleep(0.1)
print(message.getWebSearchSteps())
while not message.isDone():
    time.sleep(0.1)
print(message.getFinalText())

# get the stream text instantly
print(message.getWebSearchSteps())
print(message.getText())
```

**Code:**

```python
import os, time

from hugchat_api import HuggingChat
from hugchat_api.core import ListBots
from hugchat_api.utils import formatHistory, formatConversations

EMAIL = os.getenv("EMAIL")
PASSWD = os.getenv("PASSWD")
COOKIE_STORE_PATH = "./usercookies"

'''create ThreadPool'''
HUG = HuggingChat(max_thread=1)


'''initialize sign in funciton'''
sign = HUG.getSign(EMAIL, PASSWD)

'''sign in or...'''
cookies = sign.login(save=True, cookie_dir_path=COOKIE_STORE_PATH)
# cookies = sign.loadCookiesFromDir()



'''create bot with MetaAI's model'''
bot = HUG.getBot(email=EMAIL, cookies=cookies, model=ListBots.META_70B_HF)

'''get all conversations and see one's title'''
conversations = bot.getConversations()
conv_id = list(conversations.keys())[0]
print(conversations[conv_id])

'''get all chat histories by conversation_id'''
histories = bot.getHistoriesByID(conversation_id=conv_id)
print(formatHistory(histories))

'''delete a conversation'''
bot.removeConversation(conversation_id=conv_id)

'''create a new conversation'''
conversation_id = bot.createConversation()

'''chat'''
message = bot.chat(
    text="hi",
    conversation_id=conversation_id,
    web_search=True,
    max_tries=2,
    # callback=(bot.updateTitle, (conversation_id,))
)



'''wait the full text or...'''
while not message.web_search_done:
    time.sleep(0.1)
print(message.getWebSearchSteps())
while not message.isDone():
    time.sleep(0.1)
print(message.getFinalText())

'''get the stream text instantly'''
print(message.getWebSearchSteps())
print(message.getText())
```

</details>


<details>

<summary>

## Terminal Usage

</summary>


### Start up
```shell
python -m hugchat_api.terminal_cli -u your_email
```

| Params | Descriptions                      |
|--------|-----------------------------------|
| -u     | Login Email                       |
| -p     | Use password or not (optional)    |
| -f     | Ignore the saved cookie and login |

### Commands
Use `/` + `command` to execute commands:

| Commands   | Descriptions                           |
|------------|----------------------------------------|
| q/exit     | Exit the program                       |
| ls         | List all conversations                 |
| cd <index> | cd into the chosen conversation        |
| new        | Create a new conversation              |
| rm <index> | delete the chosen conversation         |
| old        | Print out the conversation's histories |
| web        | Switch 'Search Web' enable option      |

Anything not start with `/` will be seen as chat message.

Example:
```text
(None) > /ls
#* Conversations established:
#
#       0. [649471fa525d2d2474973871] - Hello there! How can I help you? Let me know if you need something specific done.
#       1. [64946fb2525d2d247497382c] - Hi there! How can I assist you?

(None) > /cd 0
(647e09ccabd9de3d82d6fba0) > hi
#(user): hi
#(HFBot): ...
(647e09ccabd9de3d82d6fba0) > /web
#WEB_SEARCH is set to `True`
(647e09ccabd9de3d82d6fba0) > hi
# ...(steps about web search)
#(HFBot): ...
```

</details>

## Download status
seperated in regions(country_code). powered by bigquery and mermaid.
![test](http://47.94.146.109:8000/.md)
