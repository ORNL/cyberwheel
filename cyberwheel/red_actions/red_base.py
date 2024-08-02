from __future__ import annotations
from abc import abstractmethod
from typing import Union, List, Dict, Any
from cyberwheel.detectors.alert import Alert
from cyberwheel.network.host import Host
from cyberwheel.network.service import Service
from cyberwheel.network.subnet import Subnet

targets = Union[List[Host], List[Subnet]]
destination = Union[Host, Service]
source = Union[Host, None]


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
    attack_success: bool
    metadata: Dict[str, Any]
    src_host: Host
    target_host: Host
    cost: int

    def __init__(self, src_host : Host, target_host : Host):
        self.discovered_hosts = []
        self.detector_alert = Alert(None, [], [])
        self.attack_success = False
        self.metadata = {}
        self.src_host = src_host
        self.target_host = target_host
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
        if isinstance(dst, Host):
            if dst != None:
                self.detector_alert.add_dst_host(dst)
            if src != None:
                self.detector_alert.add_src_host(src)
        elif isinstance(dst, Service):
            self.detector_alert.add_service(dst)
        else:
            raise TypeError(
                f"RedActionResults.modify_alert(): dst needs to be Host or Service not {type(dst)}"
            )

    def add_successful_action(self) -> None:
        """
        Adds the host to the list of successful actions

        - `host`: a Host where this action was successful
        """
        self.attack_success = True

    def add_metadata(self, key: str, value: Any) -> None:
        if key in self.metadata:
            for k, v in value.items():
                self.metadata[key][k] = v
        else:
            self.metadata[key] = value

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

class ARTAction:
    """
    Base class for defining Atomic Red Team actions. New ART actions should inherit from this class and define sim_execute().
    """

    def __init__(self, src_host: Host, target_host: Host) -> None:
        """
        - `src_host`: Host from which the attack originates.

        - `target_service`: The service being targeted.

        - `target_hosts`: The hosts being targeted. Can either be a list of hosts or list of subnets. If it is a list of subnets, then the attack should target all known hosts on that subnet.

        - `techniques`: A list of techniques that can be used to perform this attack.
        """
        self.src_host = src_host
        self.target_host = target_host
        self.action_results = RedActionResults(src_host, target_host)
        self.name = ""

    @abstractmethod
    def sim_execute(self) -> RedActionResults | type[NotImplementedError]:
        pass

    def get_techniques(self):
        return self.techniques

    @classmethod
    def get_name(cls):
        return cls.name
