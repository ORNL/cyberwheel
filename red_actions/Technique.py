from typing import List

class Technique():
    mitre_id : str = ""
    name : str = ""
    technique_id : str = ""
    data_components : List[str] = []
    kill_chain_phases : List[str] = []
    data_source_platforms : List[str] = []
    mitigations : List[str]= []
    description : str = ""
    atomic_tests : List[str] = []

    def get_parent_technique(self) -> str:
        if "." in self.name:
            return self.name.split(".")[0]
        else:
            return ""

class AtomicTest():
    def __init__(atomic_test_list):
        return NotImplementedError