from abc import abstractmethod
from typing import Union, List, Dict, Any
from cyberwheel.network.network_object import NetworkObject
from cyberwheel.detectors.alert import Alert
from cyberwheel.network.network_base import Network
from cyberwheel.network.host import Host
from cyberwheel.network.service import Service
from cyberwheel.network.subnet import Subnet
from .technique import Technique

targets = Union[List[Host], List[Subnet]]
destination = Union[Host, Service]
source = Union[Host, None]


def check_vulnerability(service: Service, techniques: List[Technique]) -> bool:
    """
    Checks to see if the action can be used with the given service. This is accomplished by checking the techniques' cves against the service's cves.

    - `service`: the target service

    - `techniques`: list of techniques the red agent can use with this action
    """
    for technique in techniques:
        for vulnerability in service.vulnerabilities:
            if vulnerability in technique.cve_list:
                return True
    return False


def validate_attack(host: Host, service: Service) -> bool:
    """
    Checks if the action can be taken against the given host. This is done by checking if the given service is in the host's set of services.

    - `host`: a target host

    - `service`: a target service
    """
    return True
    # return True if service in host.services else False


class RedActionResults:
    """
    A class for handling the results of a red action. The point of this class is to provide feedback to both the red and blue agents. The red agent could use `discovered_hosts` and `attack_success`
    for determining its next action and maybe even for training. The blue agent will use `detector_alert` in the form of an observation vector that is created later by a `Detector` and an `AlertsConversion`.

    Important member variables:
    - `discovered_hosts`: List of hosts discovered by this attack

    - `detector_alert`: The alert to be passed to the detector. It should contain all the information the detector can get.

    - `attack_success`: Feedback for the red agent so that it knows if the attack worked or not. Most attacks target 1 host, but some techniques, particularly reconnaissance techniques, may target multiple hosts.

    - `metadata`: Associated metadata with the red action. For example, a Reconnaissance action will add the host vulnerabilities to the metadata object.
    """

    discovered_hosts: List[Host]
    detector_alert: Alert
    attack_success: List[Host]
    metadata: Dict[str, Any]
    cost: int

    def __init__(self):
        self.discovered_hosts = []
        self.detector_alert = Alert(None, [], [])
        self.attack_success = []
        self.metadata = {}
        self.cost = 0

    def add_host(self, host: Host) -> None:
        """
        Adds a host to the list of hosts discovered by this action. The agent can later update it's known hosts using this list.

        - `host`: a host that was discovered by this action
        """
        self.discovered_hosts.append(host)

    def modify_alert(self, dst: destination, src: source = None) -> None:
        """
        Modifies the RedActionResults' alert by adding either to alert.dst_hosts or alert.services. It selects which list to modify by the type of dst which is either a Host or Service object.

        - `dst`: a Host or Service object to be added to the alert
        """
        # if isinstance(dst, Host):
        if dst != None:
            self.detector_alert.add_dst_host(dst)
        if src != None:
            self.detector_alert.add_src_host(src)
        # elif isinstance(dst, Service):
        #     self.detector_alert.add_service(dst)
        # else:
        #     raise TypeError(
        #         f"RedActionResults.modify_alert(): dst needs to be Host or Service not {type(dst)}"
        #     )

    def add_successful_action(self, host: Host) -> None:
        """
        Adds the host to the list of successful actions

        - `host`: a Host where this action was successful
        """
        self.attack_success.append(host)

    def add_metadata(self, host_or_subnet_name: str, metadata: Any) -> None:
        self.metadata[host_or_subnet_name] = metadata

    def set_cost(self, cost) -> None:
        self.cost = cost

    def __eq__(self, __value: object) -> bool:
        assert isinstance(__value, RedActionResults)
        if (
            self.discovered_hosts == __value.discovered_hosts
            and self.detector_alert == __value.detector_alert
            and self.attack_success == __value.attack_success
        ):
            return True
        return False


class RedAction:
    """
    Base class for defining red actions. New actions should inherit from this class and define sim_execute().
    """
    action_cost = {
        "Discovery": -10,
        "Reconnaissance": -20,
        "LateralMovement": -50,
        "PrivilegeEscalation": -100,
        "Impact": -500,
    }
    def __init__(self, src_host: Host, target_service, target_hosts, techniques) -> None:
        """
        - `src_host`: Host from which the attack originates.

        - `target_service`: The service being targeted.

        - `target_hosts`: The hosts being targeted. Can either be a list of hosts or list of subnets. If it is a list of subnets, then the attack should target all known hosts on that subnet.

        - `techniques`: A list of techniques that can be used to perform this attack.
        """
        self.src_host = src_host
        self.target_service = target_service
        self.target_hosts = target_hosts
        self.techniques = techniques
        self.action_results = RedActionResults()

    @abstractmethod
    def sim_execute(self) -> RedActionResults | type[NotImplementedError]:
        pass

    def get_techniques(self):
        return self.techniques

    @abstractmethod
    def perfect_alert(self):
        pass
