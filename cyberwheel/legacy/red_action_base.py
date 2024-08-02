class RedAction:
    """
    Base class for defining red actions. New actions should inherit from this class and define sim_execute().
    """

    def __init__(
        self, src_host: Host, target_service, target_hosts, techniques
    ) -> None:
        """
        - `src_host`: Host from which the attack originates.

        - `target_service`: The service being targeted.

        - `target_hosts`: The hosts being targeted. Can either be a list of hosts or list of subnets. If it is a list of subnets, then the attack should target all known hosts on that subnet.

        - `techniques`: A list of techniques that can be used to perform this attack.
        """
        self.src_host = src_host
        self.target_service = target_service
        self.target_hosts = target_hosts
        self.techniques = techniques
        self.action_results = RedActionResults()
        self.decoy = False
        self.name = ""

    @abstractmethod
    def sim_execute(self) -> RedActionResults | type[NotImplementedError]:
        pass

    @abstractmethod
    def perfect_alert(self):
        pass

    def get_techniques(self):
        return self.techniques

    @classmethod
    def get_name(cls):
        return cls.name


