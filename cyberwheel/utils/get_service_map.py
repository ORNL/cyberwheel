from cyberwheel.network.network_base import Network
from cyberwheel.red_actions import art_techniques
from cyberwheel.red_actions.actions import ARTDiscovery, ARTLateralMovement, ARTPrivilegeEscalation, ARTImpact


def get_service_map(network: Network):
    """
    Function to get the service mapping based on host attributes.
    """
    killchain = [
        ARTDiscovery,
        ARTPrivilegeEscalation,
        ARTImpact,
        ARTLateralMovement,
    ]
    service_mapping = {}
    for host in network.hosts.values():
        service_mapping[host.name] = {}
        for kcp in killchain:
            service_mapping[host.name][kcp] = []
            kcp_valid_techniques = kcp.validity_mapping[host.os][kcp.get_name()]
            for mid in kcp_valid_techniques:
                technique = art_techniques.technique_mapping[mid]
                if len(host.host_type.cve_list & technique.cve_list) > 0:
                    service_mapping[host.name][kcp].append(mid)
    return service_mapping