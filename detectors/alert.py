from ipaddress import IPv4Address
from typing import List, Union, Dict
from copy import deepcopy
from network.host import Host
from network.service import Service

# TODO Needs to be updated as the network implementation changes.
class Alert():
    FIELD_NAMES = set(['src_host', 'dst_hosts', 'local_services', 'remote_services'])
    def __init__(self, src_host: Host, dst_hosts: List[Host], local_services:List[Service], remote_services: List[Service]):
        self.src_host: Host = src_host
        self.dst_hosts: List[Host] = dst_hosts

        # TODO Right now, services appear to not do anything. 
        self.local_services: List[Service] = local_services
        self.remote_services: List[Service] = remote_services

    def set_detector(self, detector_name)-> None:
        self.detector = detector_name

    def to_dict(self)-> Dict:
        d = deepcopy(self.__dict__)
        for k in self.__dict__.keys():
            if k not in self.FIELD_NAMES:
                d.pop(k)
        return d
    