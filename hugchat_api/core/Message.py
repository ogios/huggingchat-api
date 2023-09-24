from typing import List


class Message:
    def __init__(self, conversation_id: str, web_search_enabled: bool):
        self.error: Exception | None = None
        self.conversation_id: str = conversation_id
        self.done: bool = False
        self.stream_text: List[str] = []
        self.final_text: str | None = None
        self.web_search_enabled = web_search_enabled
        self.web_search_done = False
        self.web_search_steps: List = list()
        self.web_search_step = -1

        self.temp: List[str] = []
        self.count = 0
        self.threashold = 3

    def getConversation(self) -> str:
        return self.conversation_id

    def setError(self, error: Exception):
        self.error = error
        self.done = True

    def setWebSearchSteps(self, process):
        self.web_search_steps.append(process)

    def getWebSearchSteps(self):
        if self.error:
            raise self.error
        return self.web_search_steps

    def getWebSearchStep(self):
        if self.error:
            raise self.error
        if len(self.web_search_steps) - 1 > self.web_search_step:
            self.web_search_step += 1
            return self.web_search_steps[self.web_search_step - 1]
        else:
            return None

    def cleanTemp(self):
        if len(self.temp) > 0:
            self.stream_text.extend(list("".join(self.temp)))
            self.temp = []
            self.count = 0
        return

    def setText(self, text, done: bool = False):
        if not self.web_search_done:
            self.web_search_done = True
        self.temp.append(text)
        self.count += 1
        if self.count > self.threashold:
            self.cleanTemp()
        if done:
            self.cleanTemp()
            self.setFinalText("".join(self.stream_text))

    def getText(self) -> List[str]:
        if self.error:
            raise Exception(self.error)
        return self.stream_text

    def setFinalText(self, text):
        self.final_text = text
        self.done = True
        self.cleanTemp()

    def getFinalText(self) -> str | None:
        if self.error:
            raise Exception(self.error)
        return self.final_text

    def isDone(self) -> bool:
        return self.done
