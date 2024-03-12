#from dataclasses import dataclass, field
from typing_extensions import Unpack
from pydantic import BaseModel, ConfigDict, validator, PositiveInt


class Service(BaseModel):
    name: str
    port: PositiveInt
    protocol: str = 'tcp' # default to tcp
    version: str = ''
    vulns: list = [] # TODO: list[dict] here? list[Vuln]??
    description: str = ''
    decoy: bool = False


    #def __post_init__(self) -> None:
    #    pass


    def __eq__(self, other) -> bool:
        if isinstance(other, Service):
            port_matched: bool = self.port == other.port
            proto_matched: bool = self.protocol == other.protocol
            version_matched: bool = self.version == other.version
            return port_matched and proto_matched and version_matched
        return False


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


