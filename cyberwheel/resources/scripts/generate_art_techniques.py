import json
from typing import List


def generate_art_techniques():

    scripts = """from red_actions.Technique import Technique
"""
    preamble = "\ntechnique_mapping = {"
    path_to_combined_art_techniques = "../metadata/combined_art_techniques.json"
    art_techniques = {}
    mapping = {}
    temp_list = []
    with open(path_to_combined_art_techniques, "r") as f:
        art_techniques = json.load(f)
    for key in list(art_techniques.keys()):
        t = art_techniques[key]
        name = t["name"]
        name_trunc = (
            name.replace(" ", "")
            .replace("/", "")
            .replace("-", "")
            .replace("(", "")
            .replace(")", "")
        )
        mitre_id = t["external_id"]
        temp_list.append(mitre_id)
        technique_id = t["technique_id"]
        data_components = t["data_components"]
        kill_chain_phases = t["kill_chain_phases"]
        data_source_platforms = t["data_source_platforms"]
        mitigations = t["mitigations"]
        description = t["description"].replace("\n", "").replace('"', "'")
        atomic_tests = t["atomic_tests"]
        mapping[mitre_id] = name_trunc
        cwe_list = []
        cve_list = []
        mitre_to_cwe = {}
        cwe_to_cve = {}
        with open("../metadata/attack_to_cwe.json", "r") as f:
            mitre_to_cwe = json.load(f)
        with open("../metadata/cwe_to_cve.json", "r") as f:
            cwe_to_cve = json.load(f)

        mid = mitre_id.replace("T", "")
        pid = mitre_id.split(".")[0] if "." in mitre_id else mitre_id
        pid = pid.replace("T", "")

        if mid in list(mitre_to_cwe.keys()):
            cwe_list = mitre_to_cwe[mid]
            temp_cve_list = []
            for cwe in cwe_list:
                if cwe in list(cwe_to_cve.keys()):
                    temp_cve_list.extend(cwe_to_cve[cwe])
            if len(temp_cve_list) > 0:
                cve_list = list(set(temp_cve_list))
        elif pid in list(mitre_to_cwe.keys()):
            cwe_list = mitre_to_cwe[pid]
            temp_cve_list = []
            for cwe in cwe_list:
                if cwe in list(cwe_to_cve.keys()):
                    temp_cve_list.extend(cwe_to_cve[cwe])
            if len(temp_cve_list) > 0:
                cve_list = list(set(temp_cve_list))

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
            atomic_tests={atomic_tests},
            cve_list={cve_list},
            cwe_list={cwe_list}
        )
"""
        preamble += f"'{mitre_id}': {name_trunc}, "
        # with open('temp_techniques_list.json', 'w') as f:
        #   json.dump(list(set(temp_list)), f)
    preamble = preamble[:-2] + "}\n"
    scripts = scripts + preamble
    with open("temp_techniques.py", "w") as f:
        f.write(scripts)


if __name__ == "__main__":
    generate_art_techniques()
