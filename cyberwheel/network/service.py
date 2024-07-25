from pydantic import BaseModel, validator, PositiveInt
from typing import Any, TypeVar, Type

# this allows return type hints to work with @classmethods
# https://stackoverflow.com/a/44644576
T = TypeVar("T", bound="Service")


# TODO
class Vuln(BaseModel):
    name: str
    id: str

    def __key(self):
        return (self.name, self.id)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other) -> bool:
        if isinstance(other, Vuln):
            name_matched: bool = self.name == other.name
            id_matched: bool = self.id == other.id
            return name_matched and id_matched
        return False

    # @validator('id')
    # @classmethod
    # def validate_id(cls, id: str) -> int:
    #    if port not in range(2**16):
    #        msg = 'Port should be an integer (1-65535)'
    #        raise PortValueError(value=port, message=msg)
    #    return port


class Service(BaseModel):
    name: str
    port: PositiveInt = 1  # default value so we can omit port for ICMP
    protocol: str = "tcp"
    version: str | None = None
    vulns: set[str] = set()
    description: str | None = None
    decoy: bool | None = False

    def __key(self):
        return (
            self.name,
            self.port,
            self.protocol,
            self.version,
            self.description,
            self.decoy,
        )

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other) -> bool:
        if isinstance(other, Service):
            port_matched: bool = self.port == other.port
            proto_matched: bool = self.protocol == other.protocol
            version_matched: bool = self.version == other.version
            return port_matched and proto_matched and version_matched
        return False

    @validator("port")
    @classmethod
    def validate_port(cls, port: PositiveInt) -> int:
        if port not in range(2**16):
            msg = "Port should be an integer (1-65535)"
            raise PortValueError(value=port, message=msg)
        return port

    @validator("protocol")
    @classmethod
    def validate_proto(cls, proto) -> str:
        if proto not in ["tcp", "udp", "icmp"]:
            msg = "Protocol should be 'tcp', 'udp', or 'icmp'"
            raise ProtocolValueError(value=proto, message=msg)
        return proto

    # using classmethod here only so I don't have to hard code `Service`
    @classmethod
    def create_service_from_dict(cls: Type[T], service: dict[str, Any]) -> T:
        # instantiate any defined Vulns
        vulns = service.get("cve", [])
        # vulns = [cls.create_vuln_from_list(v) for v in service_vulns]

        return Service(
            name=service.get("name"),  # type: ignore
            port=service.get("port", 1),  # type: ignore
            protocol=service.get("protocol", "tcp"),  # type: ignore
            version=service.get("version"),  # type: ignore
            vulns=vulns,
            description=service.get("description"),  # type: ignore
            decoy=service.get("decoy"),
        )  # type: ignore

    # using classmethod here only so I don't have to hard code `Service`
    @classmethod
    def create_service_from_yaml(
        cls: Type[T], service_objs: list[dict[str, Any]], service_str: str
    ) -> T:
        # instantiate any defined Vulns
        service = service_objs.get(service_str, {})
        vulns = service.get("cve", set())
        # vulns = [cls.create_vuln_from_list(v) for v in service_vulns]

        return Service(
            name=service_str,  # type: ignore
            port=service.get("port", 1),  # type: ignore
            protocol=service.get("protocol", "tcp"),  # type: ignore
            version=service.get("version"),  # type: ignore
            vulns=set(vulns),
            description=service.get("description"),  # type: ignore
            decoy=service.get("decoy"),
        )  # type: ignore

    # @staticmethod
    # def create_vuln_from_str(vuln: str):
    #    return Vuln(name=vuln, id=vuln)


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
