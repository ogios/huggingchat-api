class ConversationNotExistError(Exception):
    NotInMap: str = "The given conversation is not in the map: --id--"

class FillDataException(Exception):
    pass

class CoroutinThreadErr(Exception):
    pass
