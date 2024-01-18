import json
from typing import List

def generate_art_techniques():
    scripts = """from typing import List
from Technique import Technique, AtomicTest
"""
    path_to_combined_art_techniques = "../metadata/combined_art_techniques.json"
    art_techniques = {}
    with open(path_to_combined_art_techniques, 'r') as f:
        art_techniques = json.load(f)
    for key in list(art_techniques.keys()):
        t = art_techniques[key]
        name = t["name"]
        name_trunc = name.replace(" ", "").replace("/","").replace("-","").replace("(", "").replace(")", "")
        mitre_id = t["external_id"]
        technique_id = t["technique_id"]
        data_components = t["data_components"]
        kill_chain_phases = t["kill_chain_phases"]
        data_source_platforms = t["data_source_platforms"]
        mitigations = t["mitigations"]
        description = t["description"].replace("\n", "").replace('"', "'")
        atomic_tests = t["atomic_tests"]
        scripts += f"""
class {name_trunc}(Technique):
    mitre_id : str = "{mitre_id}"
    name : str = "{name}"
    technique_id : str = "{technique_id}"
    data_components : List[str] = {data_components}
    kill_chain_phases : List[str] = {kill_chain_phases}
    data_source_platforms : List[str] = {data_source_platforms}
    mitigations : List[str] = {mitigations}
    description : str = "{description}"
    atomic_tests : List[AtomicTest] = [AtomicTest(at) for at in {atomic_tests}]
"""
        with open('temp_techniques.py', 'w') as f:
            f.write(scripts)
if __name__ == "__main__":
    generate_art_techniques()