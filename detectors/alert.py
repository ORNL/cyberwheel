from ipaddress import IPv4Address
from typing import List, Union, Dict
from copy import deepcopy
from network.host import Host
from network.service import Service

# TODO Needs to be updated as the network implementation changes.
class Alert():
    FIELD_NAMES = set(['src_host', 'dst_hosts', 'services'])
    def __init__(self, src_host: Host = None, dst_hosts: List[Host] = [], services: List[Service]=[]):
        self.src_host: Host = src_host
        self.dst_hosts: List[Host] = dst_hosts
        self.services: List[Service] = services

    def add_dst_host(self, host: Host) -> None:
        self.dst_hosts.append(host)

    def add_service(self, service: Service) -> None:
        self.services.append(service)

    def set_detector(self, detector_name) -> None:
        self.detector = detector_name

    def to_dict(self)-> Dict:
        d = deepcopy(self.__dict__)
        for k in self.__dict__.keys():
            if k not in self.FIELD_NAMES:
                d.pop(k)
        return d
    
    def __eq__(self, __value: object) -> bool:
        src_host = True if self.src_host == __value.src_host else False
        dst_hosts = True if len(self.dst_hosts) == len(__value.dst_hosts) else False
        if dst_hosts:
            for host in self.dst_hosts:
                if host not in __value.dst_hosts:
                    dst_hosts = False
        services = True if len(self.services) == len(__value.services) else False
        if services:
            for service in self.services:
                if service not in __value.services:
                    services = False
        if src_host and dst_hosts and services:
            return True
        return False 
    