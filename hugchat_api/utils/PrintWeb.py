import time, typing
from dataclasses import dataclass
from hugchat_api.core.Message import Message
from hugchat_api.utils import color


def printWait() -> typing.Callable:
    tick = time.time()
    index = 0
    count = 3
    dots = "·.."

    def c() -> str:
        nonlocal tick, index, dots
        if time.time() - tick >= 0.5:
            tick = time.time()
            content = ["."] * count
            content[index] = "·"
            index = (index + 1) % count
            dots = "".join(content)
            # print(f"\r{dots}", flush=True, end="")
        return dots

    return c


@dataclass
class PrintWeb:
    message: Message

    def update(self):
        if not self.message.web_search_enabled:
            return
        dots = printWait()
        while 1:
            done = self.message.web_search_done
            step = self.message.getWebSearchStep()
            if done and not step:
                return
            else:
                if step:
                    if step["messageType"] == "update":
                        string = f"{step['message']}"
                        if step.__contains__("args"):
                            string += f": {str(step['args'])}"
                        print(string, flush=True)
            print(dots(), flush=True, end="\r")
            time.sleep(0.1)
        return

    def sources(self):
        if not self.message.web_search_enabled:
            return
        string = ""
        data = self.message.getWebSearchSteps()
        if not data:
            return
        data = data[-1]
        if not data or not data.__contains__("sources"):
            return
        data = data["sources"]
        for sou in data:
            sep = f"""
 {color("*", "green")} {sou['title']} - {sou['hostname']}:
    {sou['link']}
            """.strip()
            string += f"\n{sep}"
        print(string.strip())
        return
