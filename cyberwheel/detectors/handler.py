import bigtree
import yaml
import importlib
from typing import Iterator

from cyberwheel.detectors.detector_base import Detector
from cyberwheel.detectors.alert import Alert
from cyberwheel.network.host import Host
from cyberwheel.network.subnet import Subnet
import networkx as nx
import matplotlib.pyplot as plt

class DetectorHandler:
    def __init__(self, config: str) -> None:
        self.config = config
        self._from_config()

    def obs(self, perfect_alerts: Iterator[Alert]) -> Iterator[Alert]:
        pass

    def _create_graph(self):
        self.DG = nx.DiGraph()
    
    def _from_config(self):
        self._create_graph()
        with open(self.config, "r") as r:
            contents = yaml.safe_load(r)
        
        adjacency_list = contents["adjacency_list"]
        init_info = contents["init_info"]  

        for entry in adjacency_list:
            node = entry[0]
            detector = None
            self.DG.add_node(node, detector_output=[])
            if node != 'start' and node != 'end':
                if node not in init_info: 
                    raise KeyError(f'node {node} not defined in init_info')
                detector = import_detector(init_info[node]['module'], init_info[node]['class'], init_info[node].get('config', None))
            for child in entry[1:]:
                self.DG.add_edge(node, child, attr={"detector": detector})

        return self.DG

    def obs(self, perfect_alerts: Iterator[Alert]) -> Iterator[Alert]:
        for edge in self.DG.edges:
            node_data_view = self.DG.nodes.data("detector_output", default=[])
            next_node_input = node_data_view[edge[1]]
            if edge[0] == 'start':
                result = perfect_alerts
            else:
                input_alerts = node_data_view[edge[0]]
                detector = self.DG.get_edge_data(*edge)['attr']['detector'] 
                result = detector.obs(input_alerts)
            for r in result:
                if r not in next_node_input:
                    next_node_input.append(r)
            self.DG.add_node(edge[1], detector_output=next_node_input)
        return self.DG.nodes.data("detector_output", default=[])['end']

    def draw(self):
        plt.clf()  # clear
        nx.draw(
            self.DG,
            node_size=30,
            font_size=12,
            font_color="black",
            font_weight="bold",
            edge_color="black",
        )
        plt.savefig("detector.png")


def import_detector(module: str, class_: str, config: str | None) -> Detector:
    import_path = ".".join(["cyberwheel.detectors.detectors", module])
    m = importlib.import_module(import_path)
    detector_type = getattr(m, class_)  
    return detector_type(config) if config else detector_type()
      

def main():
    handler = DetectorHandler("/home/70d/cyberwheel/cyberwheel/resources/configs/example_detector_handler.yaml")
    handler.draw()
    s = Subnet("subnet", "192.168.0.0/24", None)
    src_host = Host("Host1", None, None)
    dst_hosts = [
        Host("Host2", s, None),
        Host("Host3", s, None),
        Host("Host4", s, None),
    ]
    alert = Alert(src_host, dst_hosts=dst_hosts, services=[])
    alert2 = Alert(src_host, dst_hosts=dst_hosts[:2], services=[])
    alert3 = Alert(src_host, dst_hosts=[dst_hosts[2]], services=[])
    perfect_alerts = [alert, alert2, alert3]
    # print(perfect_alerts)
    print(handler.obs(perfect_alerts))

if __name__ == "__main__":
    main()

# bigtree.print_tree(handler.tree)

