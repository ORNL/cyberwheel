from typing import List
from AtomicTest import AtomicTest
from pprint import pformat
import jsonpickle
import json

class Technique():
    mitre_id : str
    name : str
    technique_id : str
    data_components : List[str]
    kill_chain_phases : List[str]
    data_source_platforms : List[str]
    mitigations : List[str]
    description : str
    atomic_tests : List[AtomicTest]
    cwe_list : List[str]
    cve_list : List[str]
    is_subtechnique : bool
    parent_technique : str

    def __init__(self, mitre_id, name, technique_id, data_components, kill_chain_phases, data_source_platforms, mitigations, description, atomic_tests):
        self.mitre_id = mitre_id
        self.name = name
        self.technique_id = technique_id
        self.data_components = data_components
        self.kill_chain_phases = kill_chain_phases
        self.data_source_platforms = data_source_platforms
        self.mitigations = mitigations
        self.description = description.decode('utf-8')
        self.atomic_tests = [AtomicTest(at) for at in atomic_tests]
        self.is_subtechnique = "." in self.mitre_id
        self.parent_technique = self.mitre_id.split(".")[0] if self.is_subtechnique else self.mitre_id
        self.load_mappings()


    def load_mappings(self):
        self.cwe_list = []
        self.cve_list = []

        mitre_to_cwe = {}
        cwe_to_cve = {}
        with open('../resources/metadata/attack_to_cwe.json', 'r') as f:
            mitre_to_cwe = json.load(f)
        with open('../resources/metadata/cwe_to_cve.json', 'r') as f:
            cwe_to_cve = json.load(f)

        mid = self.mitre_id.replace("T", "")
        pid = self.get_parent_technique().replace("T", "")

        if mid in list(mitre_to_cwe.keys()):
            self.cwe_list = mitre_to_cwe[mid]
            temp_cve_list = []
            for cwe in self.cwe_list:
                if cwe in list(cwe_to_cve.keys()):
                    temp_cve_list.extend(cwe_to_cve[cwe])
            if len(temp_cve_list) > 0:
                self.cve_list = list(set(temp_cve_list))
        elif pid in list(mitre_to_cwe.keys()):
            self.cwe_list = mitre_to_cwe[pid]
            temp_cve_list = []
            for cwe in self.cwe_list:
                if cwe in list(cwe_to_cve.keys()):
                    temp_cve_list.extend(cwe_to_cve[cwe])
            if len(temp_cve_list) > 0:
                self.cve_list = list(set(temp_cve_list))

    def get_parent_technique(self) -> str:
        return self.parent_technique
        
    def get_vulnerabilities(self):
        return self.cve_list

    def get_weaknesses(self):
        return self.cwe_list

    def __str__(self):
        obj = jsonpickle.encode(self)
        return json.dumps(json.loads(obj), indent=4)
