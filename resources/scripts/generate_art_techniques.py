import json
from typing import List

def generate_art_techniques():
    scripts = """from Technique import Technique
"""
    path_to_combined_art_techniques = "../metadata/combined_art_techniques.json"
    art_techniques = {}
    temp_list = []
    with open(path_to_combined_art_techniques, 'r') as f:
        art_techniques = json.load(f)
    for key in list(art_techniques.keys()):
        t = art_techniques[key]
        name = t["name"]
        name_trunc = name.replace(" ", "").replace("/","").replace("-","").replace("(", "").replace(")", "")
        mitre_id = t["external_id"]
        temp_list.append(mitre_id)
        technique_id = t["technique_id"]
        data_components = t["data_components"]
        kill_chain_phases = t["kill_chain_phases"]
        data_source_platforms = t["data_source_platforms"]
        mitigations = t["mitigations"]
        description = t["description"].replace("\n", "").replace('"', "'")
        atomic_tests = t["atomic_tests"]
        scripts += f"""
class {name_trunc}(Technique):
    def __init__(self):
        super().__init__(
            mitre_id="{mitre_id}",
            name="{name}",
            technique_id="{technique_id}",
            data_components={data_components},
            kill_chain_phases={kill_chain_phases},
            data_source_platforms={data_source_platforms},
            mitigations={mitigations},
            description=b"{"".join(c for c in description if ord(c)<128)}",
            atomic_tests={atomic_tests}
        )
"""
        with open('temp_techniques_list.json', 'w') as f:
           json.dump(list(set(temp_list)), f)

if __name__ == "__main__":
    generate_art_techniques()