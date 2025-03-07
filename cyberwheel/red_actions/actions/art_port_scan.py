from cyberwheel.red_actions.actions.art_killchain_phase import ARTKillChainPhase
from cyberwheel.red_actions import art_techniques
from cyberwheel.network.host import Host

import random

class ARTPortScan(ARTKillChainPhase):
    """
    PortScan Killchain Phase Attack. As described by MITRE:

    Adversaries may attempt to get a listing of services running on remote hosts and local network infrastructure devices,
    including those that may be vulnerable to remote software exploitation. Common methods to acquire this information 
    include port and/or vulnerability scans using tools that are brought onto a system.
    """

    name: str = "portscan"

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
        art_technique = art_techniques.technique_mapping["T1046"]
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

        return self.action_results