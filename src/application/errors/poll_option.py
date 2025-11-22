class PollOptionNotFoundException(Exception):
    def __init__(self):
        super().__init__("Poll option not found")


class PollOptionAlreadyExistException(Exception):
    def __init__(self):
        super().__init__("Poll option already exist")
