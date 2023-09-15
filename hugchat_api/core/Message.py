import logging


class Message:
    def __init__(self, conversation_id: str, web_search_enabled: bool):
        self.done: bool = False
        self.stream_text: list = []
        self.final_text: str | None = None
        self.web_search_enabled = web_search_enabled
        self.web_search_done = False
        self.web_search_steps = list()
        self.error: Exception | None = None
        self.conversation_id: str = conversation_id
    
    def getConversation(self) -> str:
        return self.conversation_id
    
    def setError(self, error: Exception):
        self.error = error
        
    def setWebSearchSteps(self, process):
        self.web_search_steps = process
    
    # def setWebSearchSteps(self, process):
    #     logging.info(f"updating websearch: {process}")
    #     self.web_search_steps.append(process)
    
    def getWebSearchSteps(self):
        if self.error:
            raise self.error
        return self.web_search_steps
    
    def setText(self, text, done: bool = False):
        if not self.web_search_done:
            self.web_search_done = True
        self.stream_text.append(text)
        if done:
            self.done = True
    
    def getText(self) -> list:
        if self.error:
            raise Exception(self.error)
        return self.stream_text
    
    def setFinalText(self, text):
        self.final_text = text
        self.done = True
    
    def getFinalText(self) -> str | None:
        if self.error:
            raise Exception(self.error)
        return self.final_text
    
    def isDone(self) -> bool:
        return self.done
