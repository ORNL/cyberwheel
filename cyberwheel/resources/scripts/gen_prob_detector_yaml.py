import yaml
import json
import pprint

def data_components_to_technique_mapping(techniques_info):
    mapping = {}
    for technique in techniques_info:
        for dc in technique['data_components']:
            if dc in mapping:
                mapping[dc].append(technique['external_id'])
            else:
                mapping[dc] = [technique['external_id']]
    return mapping




def main():
    pp = pprint.PrettyPrinter(indent=0)
    with open("resources/metadata/all_techniques_info.json", "rb") as r:
        techniques_info = json.load(r)
    with open("resources/metadata/all_art_techniques.json", "rb") as r:
        art_info = json.load(r)
    dc_mapping = data_components_to_technique_mapping(techniques_info)
    art_techniques = list(art_info.keys())
    
    final_map = {}
    for key in dc_mapping.keys():
        for technique in art_techniques:
            if technique in dc_mapping[key]:
                final_map[key] = dc_mapping[key]
    pp.pprint(final_map)

if __name__ == "__main__":
    main()