from typing import List

from cyberwheel.red_actions.red_base import (
    RedAction,
    RedActionResults,
    validate_attack,
    check_vulnerability,
    targets,
)
from cyberwheel.red_actions.technique import Technique
from cyberwheel.network.host import Host
from cyberwheel.network.service import Service


class PortScan(RedAction):
    name = "PortScan"

    def __init__(
        self,
        src_host: Host,
        target_service: Service,
        target_hosts: targets,
        techniques: List[Technique],
    ) -> None:
        super().__init__(src_host, target_service, target_hosts, techniques)

    def sim_execute(self) -> RedActionResults:
        for host in self.target_hosts:
            # Check if the attack is valid against this specific host
            if not validate_attack(host, self.target_service):
                continue
            self.action_results.modify_alert(host)
            self.action_results.add_metadata(host.name, {"services": host.services})
            if self.target_service not in self.action_results.detector_alert.services:
                self.action_results.modify_alert(self.target_service)
            self.action_results.add_successful_action(host)
        return self.action_results
