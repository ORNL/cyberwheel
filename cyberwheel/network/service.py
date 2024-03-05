#from dataclasses import dataclass, field
from pydantic import BaseModel, validator, PositiveInt
from typing import Optional


class Service(BaseModel):
    name: str
    port: PositiveInt
    protocol: Optional[str] = 'tcp' # default to tcp
    version: Optional[str] = None
    vulns: Optional[list] = [] # TODO: list[dict] here? list[Vuln]??
    description: Optional[str] = ''
    decoy: Optional[bool] = False

    @validator('port')
    @classmethod
    def validate_port(cls, port: PositiveInt) -> int:
        if port not in range(2**16):
            msg = 'Port should be an integer (1-65535)'
            raise PortValueError(value=port, message=msg)
        return port

    @validator('protocol')
    @classmethod
    def validate_proto(cls, proto) -> str:
        if proto not in ['tcp', 'udp', 'icmp']:
            msg = "Protocol should be 'tcp', 'udp', or 'icmp'"
            raise ProtocolValueError(value=proto, message=msg)
        return proto


class PortValueError(ValueError):
    def __init__(self, value: int, message: str) -> None:
        self.value = value
        self.message = message
        super().__init__(message)


class ProtocolValueError(ValueError):
    def __init__(self, value: str, message: str) -> None:
        self.value = value
        self.message = message
        super().__init__(message)


    #def __post_init__(self) -> None:
    #    pass
