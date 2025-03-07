import yaml

from importlib.resources import files

class YAMLConfig:
    """
    Base class for YAML Configuration.
    """

    def __init__(self, config_file: str):
        self.config_file = files("cyberwheel.data.configs.environment").joinpath(
            config_file
        )

    def parse_config(self) -> None:
        with open(self.config_file, "r") as r:
            training_config = yaml.safe_load(r)
        self.__dict__.update(training_config)