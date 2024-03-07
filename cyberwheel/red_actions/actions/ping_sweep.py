from typing import List

from red_actions.red_base import RedAction, RedActionResults, validate_attack, targets
from red_actions.technique import Technique
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
            if not validate_attack(host, self.target_service):
                continue
            subnet_hosts = host.subnet.connected_hosts
            self.action_results.add_metadata(
                host.subnet, {"subnet_scanned", host.subnet}
            )
            for h in subnet_hosts:
                # Check if the attack is valid against this specific host
                self.action_results.add_host(h)
                self.action_results.modify_alert(host)
                self.action_results.add_metadata(host, host.ip_address)
                self.action_results.modify_alert(self.target_service)
                self.action_results.add_successful_action(
                    host
                )  # Add host to list of success
        return self.action_results
