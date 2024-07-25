from typing import List


class Dependency:
    def __init__(
        self,
        executor_name: str = "",
        description: str = "",
        prerequisite_command: str = "",
        get_prerequisite_command: str = "",
    ):
        self.executor_name = executor_name
        self.description = description

        if prerequisite_command != "":
            self.prerequisite_command = prerequisite_command.strip().split("\n")
        else:
            self.prerequisite_command = []

        if get_prerequisite_command != "":
            self.get_prerequisite_command = get_prerequisite_command.strip().split("\n")
        else:
            self.get_prerequisite_command = []

    def __str__(self):
        return f"""
    Dependency Executor - {self.executor_name}
    Description - {self.description}
    Prerequisite Command - {self.prerequisite_command}
    Get Prerequisite Command - {self.get_prerequisite_command}"""


class Executor:
    name: str
    command: List[str]
    cleanup_command: List[str]
    elevation_required: bool

    def __init__(
        self,
        name: str = "",
        command: str = "",
        cleanup_command: str = "",
        elevation_required=True,
    ):
        self.name = name
        self.elevation_required = elevation_required
        if command != "" and command != None:
            self.command = command.strip().split("\n")
        else:
            self.command = []
        if cleanup_command != "" and cleanup_command != None:
            self.cleanup_command = cleanup_command.strip().split("\n")
        else:
            self.cleanup_command = []


class InputArgument:
    name: str
    description: str
    type: str
    default: str
    value: str

    def __init__(self, name: str, description: str, type: str, default: str):
        self.name = name
        self.description = description
        self.type = type
        self.default = default
        self.value = default

    def set_value(self, value):
        self.value = value

    def __str__(self):
        return f"""
    name - {self.name}
    description - {self.description}
    type - {self.type}
    default - {self.default}
    value - {self.value}"""


class AtomicTest:
    # Required parameters
    # name: str  # required
    # auto_generated_guid: str  # required
    # description: str  # required
    # supported_platforms: List[str]  # required
    # executor: Executor  # required

    # Optional parameters
    # input_arguments: List[InputArgument]  # optional
    # dependency_executor_name: str  # optional
    # dependencies: List[Dependency]  # optional

    def __init__(self, atomic_test_dict):
        self.name = atomic_test_dict["name"] if "name" in atomic_test_dict else ""
        self.auto_generated_guid = (
            atomic_test_dict["auto_generated_guid"]
            if "auto_generated_guid" in atomic_test_dict
            else ""
        )
        self.description = (
            atomic_test_dict["description"] if "description" in atomic_test_dict else ""
        )
        self.supported_platforms = (
            atomic_test_dict["supported_platforms"]
            if "supported_platforms" in atomic_test_dict
            else []
        )

        executor_name = ""
        if "executor" in atomic_test_dict:
            executor = atomic_test_dict["executor"]
            executor_name = executor["name"] if "name" in executor else ""
            executor_command = (
                executor["command"] if "command" in executor else ""
            )
            executor_cleanup_command = (
                executor["cleanup_command"]
                if "cleanup_command" in executor
                else ""
            )
            executor_elevation_required = (
                executor["elevation_required"]
                if "elevation_required" in executor
                else True
            )  # TODO: Is it better for default elevation required to be T or F???

            self.executor = Executor(
                name=executor_name,
                command=executor_command,
                cleanup_command=executor_cleanup_command,
                elevation_required=executor_elevation_required,
            )
        else:
            self.executor = None

        if "input_arguments" in atomic_test_dict:
            input_arguments = atomic_test_dict["input_arguments"]
            inargs = []
            for name in input_arguments:
                arg = input_arguments[name]
                inargs.append(
                    InputArgument(name, arg["description"], arg["type"], arg["default"])
                )
            self.input_arguments = inargs
        else:
            self.input_arguments = []

        if "dependency_executor_name" in atomic_test_dict:
            self.dependency_executor_name = atomic_test_dict["dependency_executor_name"]
        else:
            self.dependency_executor_name = executor_name

        if "dependencies" in atomic_test_dict:
            dependencies = atomic_test_dict["dependencies"]
            self.dependencies = []
            for d in dependencies:
                self.dependencies.append(
                    Dependency(
                        self.dependency_executor_name,
                        d["description"],
                        d["prereq_command"],
                        d["get_prereq_command"],
                    )
                )
        else:
            self.dependencies = []

    def __str__(self):
        return f"""
        -------------------------------------------------------------
        Name: {self.name}
        Description: {self.description}
        Auto-Generated GUID: {self.auto_generated_guid}
        Supported Platforms: {self.supported_platforms}

        Executor:
        {str(self.executor)}

        Input Arguments:
        {[str(ia) for ia in self.input_arguments]}

        Dependencies:
        {[str(d) for d in self.dependencies]}
        -------------------------------------------------------------
        """
