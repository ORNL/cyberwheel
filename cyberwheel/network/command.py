class Command:
    executor: str
    content: str
    privilege: str = "user"

    def __init__(self, executor, content, privilege):
        self.executor = executor
        self.content = content
        self.privilege = privilege