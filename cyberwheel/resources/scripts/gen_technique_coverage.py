"""
Outputs csv mapping each data component to the number of techniques that it covers
"""

import csv
from pyattck import Attck


def generate_data_component_csv():
    # Create an instance of the Attck class
    attck = Attck()

    # Initialize a dictionary to store data component counts
    data_component_counts = {}

    # Iterate through all techniques and count data components
    for technique in attck.enterprise.techniques:
        for data_component in technique.data_components:
            if data_component.name in data_component_counts:
                data_component_counts[data_component.name] += 1
            else:
                data_component_counts[data_component.name] = 1

    data_component_counts = dict(
        sorted(data_component_counts.items(), key=lambda item: item[1], reverse=True)
    )

    # Write data to a CSV file
    csv_filename = "data_component_coverage.csv"
    with open(csv_filename, "w", newline="") as csv_file:
        csv_writer = csv.writer(csv_file)

        # Write header
        csv_writer.writerow(["Data Component", "Number of Techniques"])

        # Write data
        for data_component, count in data_component_counts.items():
            csv_writer.writerow([data_component, count])

    print(f"Data component counts written to '{csv_filename}'.")


if __name__ == "__main__":
    generate_data_component_csv()
