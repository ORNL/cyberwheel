from abc import abstractmethod
from typing import Union, List
from detectors.alert import Alert
from network.network_base import Network
from network.host import Host
from network.service import Service
from network.subnet import Subnet
from .Technique import Technique

targets = Union[List[Host], List[Subnet]]
destination = Union[Host, Service]

def check_vulnerability(service: Service, techniques: List[Technique], success_override=False) -> bool:
    if success_override:
        return True
    for technique in techniques:
        for vulnerability in service.vulnerabilities:
            if vulnerability in technique.cve_list:
                return True
    return False

def validate_attack(host: Host, service: Service) -> bool:
    return True if service in host.services else False

class RedActionResults():
    """ 
        A class for handling the results of a red action.
        
        Important member variables:

        \tdiscovered_hosts: List of hosts discovered by this attack

        \tdetector_alert: The alert to be passed to the detector. It should contain all the information the detector can get.

        \tattack_success: Feedback for the red agent so that it knows if the attack worked or not. Most attacks target 1 host, but some techniques, particularly reconnaissance techniques, may target multiple hosts.
    """
    discovered_hosts: List[Host]
    detector_alert: Alert
    attack_success: List[Host]
    
    def __init__(self):
        self.discovered_hosts = []
        self.detector_alert = Alert()
        self.attack_success = []
    
    def add_host(self, host: Host) -> None:
        self.discovered_hosts.append(host)
    
    def modify_alert(self, dst: destination) -> None:
        if isinstance(dst, Host):
            self.detector_alert.add_dst_host(dst)
        elif isinstance(dst, Service):
            self.detector_alert.add_service(dst)
        else:
            raise TypeError("RedActionResults.modify_alert(): dst needs to be Host or Service")
    
    def add_successful_attack(self, host: Host) -> None:
        self.attack_success.append(host)

    def __eq__(self, __value: object) -> bool:
        if self.discovered_hosts == __value.discovered_hosts and self.detector_alert == __value.detector_alert and self.attack_success == __value.attack_success:
            return True
        return False

class RedAction():
    """
    Base class for defining red actions.
    """
    src_host: Host
    target_service: Service
    target_hosts: targets
    techniques: List[Technique]
    action_results: RedActionResults
    def __init__(self, src_host, target_service, target_hosts, techniques) -> None:
        """
        src_host: Host from which the attack originates.

        target_service: The service being targeted.

        target_hosts: The hosts being targeted. Can either be a list of hosts or list of subnets. If it is a list of subnets, then the attack should target all known hosts on that subnet.

        techniques: A list of techniques that can be used to perform this attack.
        """
        self.src_host = src_host
        self.target_service = target_service
        self.target_hosts = target_hosts
        self.techniques = techniques
        self.action_results = RedActionResults()

    @abstractmethod
    def sim_execute(self) -> RedActionResults:
        pass

class PingSweep(RedAction):
    name = "PingSweep"
    def __init__(self, src_host: Host, target_service: Service, target_hosts: targets, techniques: List[Technique]) -> None:
        super().__init__(src_host, target_service, target_hosts, techniques)

    def sim_execute(self) -> RedActionResults:
        # Check if the targeted service is vulnerable to the chosen techniques
        if not check_vulnerability(self.target_service, [], success_override=True):
            # If the service is not vulnerable, then the attack cannot be performed at all
            return self.action_results
        for host in self.target_hosts:
            # Check if the attack is valid against this specific host
            if not validate_attack(host, self.target_service):
                continue
            self.action_results.add_host(host)
            self.action_results.modify_alert(host)
            self.action_results.modify_alert(self.target_service)
            self.action_results.add_successful_attack(host)
        return self.action_results
