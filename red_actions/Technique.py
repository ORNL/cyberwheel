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

    def get_parent_technique(self) -> str:
        if "." in self.name:
            return self.name.split(".")[0]
        else:
            return ""

    def __str__(self):
        obj = jsonpickle.encode(self)
        return json.dumps(json.loads(obj), indent=4)
    
    
    


"""
Technique Information:
    Name: {self.name}
    ------------------------------------------------------------------------------------------------------------------------------------------------------
    Description: {self.description}
    ------------------------------------------------------------------------------------------------------------------------------------------------------
    Mitre ID: {self.mitre_id}
    ------------------------------------------------------------------------------------------------------------------------------------------------------
    Technique ID: {self.technique_id}
    ------------------------------------------------------------------------------------------------------------------------------------------------------
    Data Components: 
    {self.data_components}
    ------------------------------------------------------------------------------------------------------------------------------------------------------
    Killchain Phases: 
    {self.kill_chain_phases}
    ------------------------------------------------------------------------------------------------------------------------------------------------------
    Data Source Platforms: 
    {self.data_source_platforms}
    ------------------------------------------------------------------------------------------------------------------------------------------------------
    Mitigations: 
    {self.mitigations}
    ------------------------------------------------------------------------------------------------------------------------------------------------------
    Atomic Tests: 
    {[pformat(str(at)) for at in self.atomic_tests]}")
    ------------------------------------------------------------------------------------------------------------------------------------------------------"""
