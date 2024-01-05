from pyattck import Attck
import json

def map_mitigations_to_techniques():

    count = 0
    components = []
    for technique in attck.enterprise.techniques:
        for component in technique.data_components:
            if component not in components:
                components.append(component)
        count+= 1

    mapping = {}
    count = 0
    for mitigation in attck.enterprise.mitigations:
        count += 1
        for technique in mitigation.techniques:
            if technique.id not in mapping:
                mapping[technique.id] = [mitigation.id]
            else:
                mapping[technique.id].append(mitigation.id)

    return mapping

def create_techniques_json():
    # Create an instance of the Attck class
    technique_to_mitigations = map_mitigations_to_techniques()

    # Initialize a list to store technique information
    techniques_info = []

    # Iterate through all techniques and gather information
    for technique in attck.enterprise.techniques:
        technique_info = {
            'name': technique.name,
            'technique_id': technique.id,
            'external_id': technique.external_references[0].external_id,
            'data_components': [dc.name for dc in technique.data_components],
            'kill_chain_phases': [phase.phase_name for phase in technique.kill_chain_phases],
            'data_source_platforms': [source.platform for source in technique.data_sources],
            'mitigations': technique_to_mitigations[technique.id] if technique.id in technique_to_mitigations else None,
            'description': technique.description
        }

        techniques_info.append(technique_info)

    # Convert the list to JSON
    json_output = json.dumps(techniques_info, indent=2)

    # Write the JSON to a file
    with open('all_techniques_info.json', 'w') as json_file:
        json_file.write(json_output)

    print("Technique information written to 'all_techniques_info.json'.")

if __name__ == "__main__":
    attck = Attck()
    create_techniques_json()