from ipaddress import IPv4Address
from typing import List, Union, Dict
from copy import deepcopy

InputAddress = Union[str, None, IPv4Address]

def _create_input_address(in_add: InputAddress) -> Union[None, IPv4Address]:
    if in_add is not None:
        return IPv4Address(in_add)

def _create_input_addresses(in_adds: List[InputAddress]) -> List[IPv4Address]:
    out_adds = []
    for in_add in in_adds:
        formatted_add = _create_input_address(in_add)
        if formatted_add is not None:
            out_adds.append(formatted_add)
    return out_adds


class Alert():
    # This list isn't complete. If it is reasonable for a detector to detect it, then add it here
    FIELD_NAMES = set(['src_ip', 'dst_ips', 'local_ports', 'remote_ports'])
    def __init__(self, src_ip: InputAddress, dst_ips: List[InputAddress], local_ports: List[int], remote_ports: List[int]):
        self.src_ip: InputAddress = _create_input_address(src_ip)
        self.dst_ips: List[IPv4Address] = _create_input_addresses(dst_ips)
        self.local_ports: List[int] = local_ports
        self.remote_ports: List[int] = remote_ports

    def set_detector(self, detector_name)-> None:
        self.detector = detector_name

    def to_dict(self)-> Dict:
        d = deepcopy(self.__dict__)
        for k in self.__dict__.keys():
            if k not in self.FIELD_NAMES:
                d.pop(k)
        return d
    