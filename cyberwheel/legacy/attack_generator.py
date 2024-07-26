"""
750 techniques, 267 mitigations, and 105 data components in enterprise.json
"""

import random
import yaml
from pyattck import Attck
import requests


def select_apt_crew():
    apt_crews = attack.enterprise.actors
    selected_crew = random.choice(apt_crews)
    return selected_crew


def select_techniques_for_stage(apt_crew, stage, num_techniques):
    techniques = apt_crew.techniques
    selected_techniques = [
        technique
        for technique in techniques
        if stage in [p.phase_name.lower() for p in technique.kill_chain_phases]
    ]

    # Randomly select up to num_techniques from the available techniques
    selected_techniques = random.sample(
        selected_techniques, min(num_techniques, len(selected_techniques))
    )

    return selected_techniques


def match_data_to_techniques(selected_techniques):
    matched_data = {}
    for technique in selected_techniques:
        data_components = [dc.name for dc in technique.data_components]
        description = technique.description
        kill_chain_phases = [phase.phase_name for phase in technique.kill_chain_phases]
        data_source_platforms = [source.platform for source in technique.data_sources]
        external_id = technique.external_references[0].external_id

        matched_data[technique.name] = {
            "data_components": data_components,
            "description": description,
            "kill_chain_phases": kill_chain_phases,
            "data_source_platforms": data_source_platforms,
            "external_id": external_id,
        }

    return matched_data


def generate_campaign(apt_crew, num_techniques_per_stage):
    campaign = []
    technique_to_mitigations = map_mitigations_to_techniques()

    # Select techniques for each stage of the kill chain
    stages = [
        "reconnaissance",
        "recource-development",
        "initial-access",
        "execution",
        "persistence",
        "privilege-escalation",
        "defense-evasion",
        "credential-access",
        "discovery",
        "lateral-movement",
        "collection",
        "command-and-control",
        "exfiltration",
        "impact",
    ]
    for stage in stages:
        selected_techniques = select_techniques_for_stage(
            apt_crew, stage, num_techniques_per_stage
        )
        if selected_techniques:
            for selected_technique in selected_techniques:

                data_info = match_data_to_techniques([selected_technique])
                campaign.append(
                    {
                        "technique": selected_technique.name,
                        "stixid": selected_technique.id,
                        "external_id": data_info[selected_technique.name][
                            "external_id"
                        ],
                        "stage": stage,
                        "data_components": data_info[selected_technique.name][
                            "data_components"
                        ],
                        "description": data_info[selected_technique.name][
                            "description"
                        ],
                        "kill_chain_phases": data_info[selected_technique.name][
                            "kill_chain_phases"
                        ],
                        "data_source_platforms": data_info[selected_technique.name][
                            "data_source_platforms"
                        ],
                        "mitigations": technique_to_mitigations[selected_technique.id],
                    }
                )

    return campaign


# 750 techniques
# 267 total mitigations
def map_mitigations_to_techniques():

    count = 0
    components = []
    for technique in attack.enterprise.techniques:
        for component in technique.data_components:
            if component not in components:
                components.append(component)
        count += 1

    mapping = {}
    count = 0
    for mitigation in attack.enterprise.mitigations:
        count += 1
        for technique in mitigation.techniques:
            if technique.id not in mapping:
                mapping[technique.id] = [mitigation.id]
            else:
                mapping[technique.id].append(mitigation.id)

    return mapping


def main():
    # Set the number of techniques to be selected from each stage
    num_techniques_per_stage = 2

    # Select an APT crew
    selected_crew = select_apt_crew()

    # Generate a campaign of attacks
    campaign = generate_campaign(selected_crew, num_techniques_per_stage)

    # Output the information in YAML format
    output_data = {"apt_crew": selected_crew.name, "campaign": campaign}

    with open("campaign_info.yaml", "w") as yaml_file:
        yaml.dump(output_data, yaml_file, default_flow_style=False, sort_keys=False)

    print("Campaign information YAML file created: campaign_info.yaml")


if __name__ == "__main__":
    attack = Attck(
        nested_techniques=True,
        enterprise_attck_json="./pyattck/merged_enterprise_attck_v1.json",
        pre_attck_json="./pyattck/merged_pre_attck_v1.json",
    )
    main()
