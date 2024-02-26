from typing import List

from red_actions.red_base import RedAction, RedActionResults, validate_attack, targets
from red_actions.Technique import Technique
from network.host import Host
from network.service import Service


class PingSweep(RedAction):
    name = "PingSweep"

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
            self.action_results.add_host(host)
            self.action_results.modify_alert(host)
            self.action_results.modify_alert(self.target_service)
            self.action_results.add_successful_action(host)
        return self.action_results
