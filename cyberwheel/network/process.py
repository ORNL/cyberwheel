from typing import Any


class Process:
    def __init__(self, name: str, privilege: str):
        self.name = name
        self.privilege = privilege

    def escalate_privilege(self):
        self.privilege = "root"

    def __eq__(self, __value: object) -> bool:
        assert isinstance(__value, Process)
        if self.name == __value.name:
            return True
        return False
