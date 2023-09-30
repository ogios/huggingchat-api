from dataclasses import dataclass
import logging
from traceback import print_exc
import traceback
from hugchat_api.core.Message import Message

import os
from wcwidth import wcswidth
import time


@dataclass
class PrintLoop:
    message: Message
    index: int = 0
    tick: float = time.time()
    tick_index: int = 0
    tick_count: int = 3
    tick_dots: str = "·.."

    def dots(self) -> str:
        if time.time() - self.tick >= 0.5:
            self.tick = time.time()
            content = ["."] * self.tick_count
            content[self.tick_index] = "·"
            self.tick_index = (self.tick_index + 1) % self.tick_count
            self.tick_dots = "".join(content)
            # print(f"\r{dots}", flush=True, end="")
        return self.tick_dots

    def get_line(self, dots: bool = False) -> str:
        if dots:
            screen_max = os.get_terminal_size().columns - 3
        else:
            screen_max = os.get_terminal_size().columns
        screen_count = 0
        ind = 0
        string = ""
        while 1:
            # breaks
            if (screen_count == screen_max) or (screen_count == screen_max - 1):
                string += "\n"
                self.index += ind
                break
            if self.index + ind >= len(self.message.stream_text) - 1:
                break

            # line
            minus = screen_max - screen_count
            ranger = int(minus / 2)
            start = self.index + ind
            if ranger < len(self.message.stream_text):
                sep = self.message.stream_text[start : start + ranger]
            else:
                sep = self.message.stream_text[start:]
            feild = "".join(sep)
            if "\n" in feild:
                break_index = (string + feild).index("\n")
                self.index += break_index + 1
                string = (string + feild)[: break_index + 1]
                break
            else:
                screen_width = wcswidth(feild)
                screen_count += screen_width
                ind += len(sep)
                string += feild
        if dots and "\n" not in string:
            return string + self.dots()
        else:
            return string

    def main(self):
        while not self.message.done:
            if len(self.message.stream_text) >= self.index:
                line = self.get_line(dots=True)
                print(line, flush=True, end="\r")
            time.sleep(0.01)
        else:
            line = self.get_line()
            print(line, flush=True)
        if self.message.error:
            traceback.print_exception(self.message.error)
            logging.debug(self.message.error)
