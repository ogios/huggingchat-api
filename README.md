# Huggingchat api

**You Star You Win A BILLION$$$(maybe,it's not impossible that it would happen)**

> This is my first pypi project. Experienced some annoying moments, but i managed to do it anyway

[![PyPI version](https://img.shields.io/pypi/v/hugchat-api.svg)](https://pypi.python.org/pypi/hugchat-api/)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/hugchat-api.svg)](https://pypi.python.org/pypi/hugchat-api/)

[![Downloads](https://static.pepy.tech/badge/hugchat-api)](https://pepy.tech/project/hugchat-api)

```shell
pip install hugchat-api
```


> [!NOTE]  
> **VERSIONS BEFORE `v0.0.1.6` ARE DEPRECATED!  PLEASE UPDATE TO THE LASTEST.**  
> For documentation, please see [Wiki](https://github.com/ogios/huggingchat-api/wiki)

## Lastest Change
- **Fix! :** response parse process (response body changed)
- **Fix! :** web search parse process (api removed)
- **Feat:** Provide stdout with `flush` that suits better for stream output
- too much changes, i forgor💀

## Screenshots
### Normal Chat
![hugchat_normal](https://github.com/ogios/huggingchat-api/assets/96933655/7068d243-62c2-4209-a132-ecf7ceb8254a)

### With Search Web
![hugchat_web](https://github.com/ogios/huggingchat-api/assets/96933655/ec818273-4849-4416-b5ea-e2c555ab1140)




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
