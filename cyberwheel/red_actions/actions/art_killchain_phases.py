from cyberwheel.red_actions.red_base import ARTAction
from cyberwheel.network.host import Host

import cyberwheel.red_actions.art_techniques as art_techniques
import random


class ARTKillChainPhase(ARTAction):
    """
    Base for defining a KillChainPhase. Any new Killchain Phase (probably not needed) should inherit from this class.
    """

    validity_mapping = {
        "windows": {
            "discovery": [
                "T1010",
                "T1217",
                "T1069.002",
                "T1482",
                "T1083",
                "T1087.002",
                "T1087.001",
                "T1615",
                "T1069.001",
                "T1046",
                "T1135",
                "T1040",
                "T1201",
                "T1120",
                "T1057",
                "T1012",
                "T1018",
                "T1518.001",
                "T1518",
                "T1497.001",
                "T1082",
                "T1614.001",
                "T1016",
                "T1049",
                "T1033",
                "T1007",
                "T1124",
            ],
            "lateral-movement": [
                "T1021.003",
                "T1570",
                "T1550.002",
                "T1550.003",
                "T1563.002",
                "T1021.001",
                "T1091",
                "T1021.002",
                "T1072",
                "T1021.006",
            ],
            "privilege-escalation": [
                "T1546.008",
                "T1547.014",
                "T1546.009",
                "T1546.010",
                "T1546.011",
                "T1055.004",
                "T1053.002",
                "T1547.002",
                "T1547",
                "T1548.002",
                "T1574.012",
                "T1546.001",
                "T1546.015",
                "T1134.002",
                "T1574.001",
                "T1574.002",
                "T1078.001",
                "T1055.001",
                "T1546",
                "T1055.011",
                "T1484.001",
                "T1546.012",
                "T1547.006",
                "T1547.008",
                "T1078.003",
                "T1547.015",
                "T1037.001",
                "T1546.007",
                "T1134.004",
                "T1574.008",
                "T1574.009",
                "T1547.010",
                "T1055.002",
                "T1546.013",
                "T1547.012",
                "T1055.012",
                "T1055",
                "T1547.001",
                "T1134.005",
                "T1053.005",
                "T1546.002",
                "T1547.005",
                "T1574.011",
                "T1547.009",
                "T1055.003",
                "T1547.003",
                "T1134.001",
                "T1546.003",
                "T1543.003",
                "T1547.004",
            ],
            "impact": [
                "T1531",
                "T1485",
                "T1486",
                "T1490",
                "T1491.001",
                "T1489",
                "T1529",
            ],
        },
        "macos": {
            "discovery": [
                "T1217",
                "T1580",
                "T1083",
                "T1087.001",
                "T1069.001",
                "T1046",
                "T1135",
                "T1040",
                "T1201",
                "T1057",
                "T1018",
                "T1518.001",
                "T1518",
                "T1497.001",
                "T1082",
                "T1016",
                "T1049",
                "T1033",
                "T1124",
            ],
            "lateral-movement": ["T1021.005"],
            "privilege-escalation": [
                "T1053.003",
                "T1078.001",
                "T1574.006",
                "T1546.014",
                "T1547.006",
                "T1543.001",
                "T1543.004",
                "T1078.003",
                "T1037.002",
                "T1547.015",
                "T1037.004",
                "T1547.007",
                "T1548.001",
                "T1037.005",
                "T1548.003",
                "T1546.005",
                "T1546.004",
            ],
            "impact": ["T1531", "T1485", "T1486", "T1496", "T1529"],
        },
        "linux": {
            "discovery": [
                "T1217",
                "T1580",
                "T1069.002",
                "T1083",
                "T1087.002",
                "T1087.001",
                "T1069.001",
                "T1046",
                "T1135",
                "T1040",
                "T1201",
                "T1057",
                "T1018",
                "T1518.001",
                "T1497.001",
                "T1082",
                "T1614.001",
                "T1016",
                "T1049",
                "T1033",
                "T1007",
                "T1124",
            ],
            "lateral-movement": [],
            "privilege-escalation": [
                "T1053.002",
                "T1053.003",
                "T1574.006",
                "T1547.006",
                "T1078.003",
                "T1037.004",
                "T1548.001",
                "T1548.003",
                "T1543.002",
                "T1053.006",
                "T1546.005",
                "T1546.004",
            ],
            "impact": ["T1531", "T1485", "T1486", "T1496", "T1529"],
        },
    }

    def __init__(
        self,
        src_host: Host = None,
        target_host: Host = None,
        valid_techniques: list[str] = [],
    ) -> None:
        """
        Same parameters as defined and described in the RedAction base class.
        - `src_host`: Host from which the attack originates.

        - `target_service`: The service being targeted.

        - `target_hosts`: The hosts being targeted. Can either be a list of hosts or list of subnets. If it is a list of subnets, then the attack should target all known hosts on that subnet.

        - `techniques`: A list of techniques that can be used to perform this attack.
        """
        super().__init__(src_host, target_host)
        self.valid_techniques = valid_techniques

    def sim_execute(self):
        self.action_results.detector_alert.add_src_host(self.src_host)
        host = self.target_host
        host_os = host.os
        self.action_results.modify_alert(dst=host)

        if len(self.valid_techniques) > 0:
            self.action_results.add_successful_action(host)
            mitre_id = random.choice(
                self.valid_techniques
            )  # Change to look for depending on service
            art_technique = art_techniques.technique_mapping[mitre_id]

            processes = []
            valid_tests = [
                at
                for at in art_technique.atomic_tests
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
                host.run_command(chosen_test.executor, p, 'root')
            self.action_results.add_metadata(
                host.name,
                {
                    "commands": processes,
                    "mitre_id": mitre_id,
                    "technique": art_technique.name,
                },
            )

        return self.action_results


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
        self.name = "pingsweep"

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
            at for at in art_technique.atomic_tests if host_os in at.supported_platforms
        ]
        chosen_test = random.choice(valid_tests)
        # Get prereq command, prereq command (if dependency). then run executor command(s) and cleanup command.
        for dep in chosen_test.dependencies:
            processes.extend(dep.get_prerequisite_command)
            processes.extend(dep.prerequisite_command)
        if chosen_test.executor != None:
            processes.extend(chosen_test.executor.command)
            processes.extend(chosen_test.executor.cleanup_command)

        self.action_results.add_successful_action(host)
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
        for h in interfaces:
            self.action_results.add_metadata(h.name, {"ip_address": h})

        return self.action_results


class ARTPortScan(ARTKillChainPhase):
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

    name: str = "portscan"

    def __init__(
        self,
        src_host: Host,
        target_host: Host,
    ) -> None:
        super().__init__(src_host, target_host)
        self.name = "portscan"

    def sim_execute(self):
        self.action_results.detector_alert.add_src_host(self.src_host)
        host = self.target_host
        self.action_results.modify_alert(dst=host)

        host_os = host.os
        action_type = self.name
        art_technique = art_techniques.technique_mapping["T1046"]
        mitre_id = art_technique.mitre_id
        processes = []
        valid_tests = [
            at for at in art_technique.atomic_tests if host_os in at.supported_platforms
        ]
        chosen_test = random.choice(valid_tests)
        # Get prereq command, prereq command (if dependency). then run executor command(s) and cleanup command.
        for dep in chosen_test.dependencies:
            processes.extend(dep.get_prerequisite_command)
            processes.extend(dep.prerequisite_command)
        if chosen_test.executor != None:
            processes.extend(chosen_test.executor.command)
            processes.extend(chosen_test.executor.cleanup_command)
        self.action_results.add_successful_action(host)
        self.action_results.add_metadata(
            host.name,
            {
                "commands": processes,
                "mitre_id": mitre_id,
                "technique": art_technique.name,
            },
        )

        return self.action_results


class ARTPrivilegeEscalation(ARTKillChainPhase):
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

    name: str = "privilege-escalation"

    def __init__(
        self, src_host: Host, target_host: Host, valid_techniques: list[str] = []
    ) -> None:
        super().__init__(src_host, target_host, valid_techniques=valid_techniques)
        self.name = "privilege-escalation"


class ARTDiscovery(ARTKillChainPhase):
    """
    Discovery Killchain Phase Attack. As described by MITRE:

    The adversary is trying to figure out your environment.

    Discovery consists of techniques an adversary may use to gain knowledge about the system and internal network.
    These techniques help adversaries observe the environment and orient themselves before deciding how to act.
    They also allow adversaries to explore what they can control and what's around their entry point in order to
    discover how it could benefit their current objective. Native operating system tools are often used toward
    this post-compromise information-gathering objective.
    """

    name: str = "discovery"

    def __init__(
        self, src_host: Host, target_host: Host, valid_techniques: list[str] = []
    ) -> None:
        super().__init__(src_host, target_host, valid_techniques=valid_techniques)
        self.name = "discovery"

    def sim_execute(self):
        super().sim_execute()
        if self.target_host in self.action_results.attack_success:
            self.action_results.add_metadata(
                self.target_host.name,
                {"type": self.target_host.host_type.name},
            )
        return self.action_results


class ARTLateralMovement(ARTKillChainPhase):
    """
    LateralMovement Killchain Phase Attack. As described by MITRE:

    The adversary is trying to move through your environment.

    Lateral Movement consists of techniques that adversaries use to enter and control remote systems on a network.
    Following through on their primary objective often requires exploring the network to find their target and
    subsequently gaining access to it. Reaching their objective often involves pivoting through multiple systems
    and accounts to gain. Adversaries might install their own remote access tools to accomplish Lateral Movement
    or use legitimate credentials with native network and operating system tools, which may be stealthier.
    """

    name: str = "lateral-movement"

    def __init__(
        self, src_host: Host, target_host: Host, valid_techniques: list[str] = []
    ) -> None:
        super().__init__(src_host, target_host, valid_techniques=valid_techniques)
        self.name = "lateral-movement"


class ARTImpact(ARTKillChainPhase):
    """
    Impact Killchain Phase Attack. As described by MITRE:

    The adversary is trying to manipulate, interrupt, or destroy your systems and data.

    Impact consists of techniques that adversaries use to disrupt availability or compromise integrity by manipulating business and
    operational processes. Techniques used for impact can include destroying or tampering with data. In some cases, business processes
    can look fine, but may have been altered to benefit the adversaries' goals. These techniques might be used by adversaries to follow
    through on their end goal or to provide cover for a confidentiality breach.
    """

    name: str = "impact"

    def __init__(
        self, src_host: Host, target_host: Host, valid_techniques: list[str] = []
    ) -> None:
        super().__init__(src_host, target_host, valid_techniques=valid_techniques)
        self.name = "impact"
