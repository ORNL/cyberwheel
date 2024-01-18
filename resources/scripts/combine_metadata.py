import json
import sys

def combine_metadata(path_to_all_techniques_info : str, path_to_all_art_techniques : str):
    art_techniques = {}
    technique_info = {}
    with open(path_to_all_art_techniques, 'r') as f:
        art_techniques = json.load(f) # Has 298 techniques
    with open(path_to_all_techniques_info, 'r') as f:
        technique_info = json.load(f) # Has 750 techniques
    
    t_names = [t["external_id"] for t in technique_info]
    art_names = list(art_techniques.keys())

    combined_dict = {}
    for i in range(len(t_names)):
       if t_names[i] in art_names:
            t = t_names[i]
            combined_dict[t] = technique_info[i]
            combined_dict[t]["atomic_tests"] = art_techniques[t]["atomic_tests"]
    
    with open('combined_art_techniques.json', 'w') as f:
        json.dump(combined_dict, f)

if __name__ == "__main__":
    combine_metadata(sys.argv[1], sys.argv[2]) # First arg is path to all_techniques_info.json, second arg is path to all_art_techniques.json