# Huggingchat api
> I will be glad if this works perfectly and you also like it. I did as much as possible to make it works perfectly on my machine.


## Sign in
Here's a example of how to log into huggingface and get cookies
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
bot = HUG.getBot(email=EMAIL, cookies=cookies)
```
- Get all conversations & Print title
```python
conversations = bot.getConversations()
print(conversations[0]["title"])
```
- Get all chat histories by conversation_id
```python
histories = bot.getHistoriesByID(conversation_id=conversations[0]["id"])
print(formatHistory(histories))
```
- Delete a conversation
```python
bot.removeConversation(index=0)
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
    callback=(bot.updateTitle, (conversation_id,))
)
# wait the full text or...
while not message.isDone():
    time.sleep(0.1)
print(message.getWebSearchSteps())
print(message.getFinalText())
# get the stream text instantly
print(message.getWebSearchSteps())
print(message.getText())
```

**Code:**

```python
import os, time
from hugchat_api import HuggingChat
from hugchat_api.utils import formatHistory, formatConversations

EMAIL = os.getenv("EMAIL_QQ")
PASSWD = ""
COOKIE_STORE_PATH = "./usercookies"

# create ThreadPool
HUG = HuggingChat(max_thread=1)       

# initialize sign in funciton
sign = HUG.getSign(EMAIL, PASSWD)   
# sign in or...
cookies = sign.login(save=True, cookie_dir_path=COOKIE_STORE_PATH)
# create bot
bot = HUG.getBot(email=EMAIL, cookies=cookies)
# get all conversations and see one's title
conversations = bot.getConversations()
print(conversations[0]["title"])
# get all chat histories by conversation_id
histories = bot.getHistoriesByID(conversation_id=conversations[0]["id"])
print(formatHistory(histories))
# delete a conversation
bot.removeConversation(index=0)
# create a new conversation
conversation_id = bot.createConversation()
# chat
message = bot.chat(
    text="hi",
    conversation_id=conversation_id,
    web_search=True,
    max_tries=2,
    callback=(bot.updateTitle, (conversation_id,))
)
# wait the full text or...
while not message.isDone():
    time.sleep(0.1)
print(message.getWebSearchSteps())
print(message.getFinalText())
# get the stream text instantly
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
#* Conversations that have been established:
#
#        0. Assistant: "It's February 24th."
#        1. Today is Wednesday, July 12th, 2034
#        2. "What is today's date?"
#        3. "April 2nd."
#

(None) > /cd 0
(647e09ccabd9de3d82d6fba0) > hi
#(user): hi
#(Open-Assistant): ...
(647e09ccabd9de3d82d6fba0) > /web
#WEB_SEARCH is set to `True`
(647e09ccabd9de3d82d6fba0) > hi
# ...(steps about web search)
#(Open-Assistant): ...
```

</details>