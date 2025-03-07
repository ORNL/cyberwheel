from cyberwheel.red_actions.actions.art_killchain_phase import ARTKillChainPhase
from cyberwheel.red_actions import art_techniques
from cyberwheel.network.host import Host

import random

class ARTPingSweep(ARTKillChainPhase):
    """
    PrivilegeEscalation Killchain Phase Attack. As described by MITRE:

    The adversary is trying to gain higher-level permissions.

    Privilege Escalation consists of techniques that adversaries use to gain higher-level permissions on a system or network.
    Adversaries can often enter and explore a network with unprivileged access but require elevated permissions to follow
    through on their objectives. Common approaches are to take advantage of system weaknesses, misconfigurations, and
    vulnerabilities. Examples of elevated access include:
    - SYSTEM/root level
    - local administrator
    - user account with admin-like access
    - user accounts with access to specific system or perform specific function

    These techniques often overlap with Persistence techniques, as OS features that let an adversary persist can execute in an elevated context.
    """

    name: str = "pingsweep"

    def __init__(
        self,
        src_host: Host,
        target_host: Host,
    ) -> None:
        super().__init__(src_host, target_host)
        self.action_results.action = type(self)

    def sim_execute(self):
        self.action_results.detector_alert.add_src_host(self.src_host)
        host = self.target_host
        self.action_results.modify_alert(dst=host)

        host_os = host.os
        action_type = self.name
        art_technique = art_techniques.technique_mapping["T1018"]
        mitre_id = art_technique.mitre_id
        processes = []
        valid_tests = [
            at
            for at in art_technique.get_atomic_tests()
            if host_os in at.supported_platforms
        ]
        chosen_test = random.choice(valid_tests)
        # Get prereq command, prereq command (if dependency). then run executor command(s) and cleanup command.
        for dep in chosen_test.dependencies:
            processes.extend(dep.get_prerequisite_command)
            processes.extend(dep.prerequisite_command)
        if chosen_test.executor != None:
            processes.extend(chosen_test.executor.command)
            processes.extend(chosen_test.executor.cleanup_command)
        for p in processes:
            host.run_command(chosen_test.executor, p, "user")

        self.action_results.add_successful_action()
        self.action_results.add_metadata(
            host.name,
            {
                "commands": processes,
                "mitre_id": mitre_id,
                "technique": art_technique.name,
            },
        )

        subnet_hosts = host.subnet.connected_hosts
        interfaces = []
        self.action_results.add_metadata(
            host.subnet.name, {"subnet_scanned": host.subnet}
        )
        for each_host in subnet_hosts:
            for h in each_host.interfaces:
                interfaces.append(h)
        #for h in interfaces:
        #    self.action_results.add_metadata(h.name, {"ip_address": h})
        sweeped_hosts = subnet_hosts + interfaces
        self.action_results.add_metadata(
            "sweeped_hosts", sweeped_hosts
        )
        self.action_results.add_metadata(
            "interfaced_hosts", [h.name for h in interfaces]
        )
        return self.action_results