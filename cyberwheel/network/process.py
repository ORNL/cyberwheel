from typing import Any
from pydantic import BaseModel, validator


class Process(BaseModel):
    name: str
    privilege: str = "user"

    def __key(self):
        return (self.name, self.privilege)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other) -> bool:
        if isinstance(other, Process):
            name_matched: bool = self.name == other.name
            privilege_matched: bool = self.privilege == other.privilege
            return name_matched and privilege_matched
        return False

    @validator("privilege")
    @classmethod
    def validate_privilege(cls, priv) -> str:
        if priv not in ["user", "root"]:
            msg = "Privilege level should be 'user' or 'root'"
            raise PrivilegeValueError(value=priv, message=msg)
        return priv

    def escalate_privilege(self):
        self.privilege = "root"


class PrivilegeValueError(ValueError):
    def __init__(self, value: str, message: str) -> None:
        self.value = value
        self.message = message
        super().__init__(message)
