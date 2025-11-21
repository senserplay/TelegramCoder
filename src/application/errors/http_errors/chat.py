class ChatNotFoundException(Exception):
    def __init__(self):
        super().__init__("Chat not found")


class ChatAlreadyExistException(Exception):
    def __init__(self):
        super().__init__("Chat already exist")
