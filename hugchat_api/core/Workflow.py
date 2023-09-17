from abc import abstractmethod, ABCMeta


class Workflow(metaclass=ABCMeta):

    @abstractmethod
    async def run(self):
        pass
