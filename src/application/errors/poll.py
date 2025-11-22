class PollNotFoundException(Exception):
    def __init__(self):
        super().__init__("Poll not found")


class PollAlreadyExistException(Exception):
    def __init__(self):
        super().__init__("Poll already exist")
