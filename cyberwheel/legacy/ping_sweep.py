from typing import List

from cyberwheel.red_actions.red_base import (
    RedAction,
    RedActionResults,
    targets,
)
from cyberwheel.red_actions.technique import Technique
from cyberwheel.network.host import Host
from cyberwheel.network.service import Service


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
        # self.action_results.modify_alert(src=self.src_host)
        self.action_results.detector_alert.add_src_host(self.src_host)
        for host in self.target_hosts:
            subnet_hosts = host.subnet.connected_hosts
            self.action_results.modify_alert(dst=host)
            self.action_results.add_metadata(
                host.subnet.name, {"subnet_scanned": host.subnet}
            )
            for h in host.interfaces:
                subnet_hosts.append(h)
            for h in subnet_hosts:
                # Check if the attack is valid against this specific host
                # self.action_results.add_host(h)
                # self.action_results.modify_alert(host)
                self.action_results.add_metadata(
                    host.name, {"ip_address": host.ip_address}
                )
                self.action_results.modify_alert(self.target_service)
                self.action_results.add_successful_action(
                    host
                )  # Add host to list of success
        return self.action_results
