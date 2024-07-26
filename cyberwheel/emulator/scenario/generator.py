import yaml

with open("example_config.yaml", 'r') as file:
    data = yaml.load(file, Loader=yaml.SafeLoader)

print(data.get("network"))
