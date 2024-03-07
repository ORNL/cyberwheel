from redagents.red_agent_base import RedAgent
from typing import Dict, List


class ARTCampaign(RedAgent):
    """
    Class defining an ART Campaign. Acts as a tailor-made killchain with specific
    pre-defined MITRE Techniques rather than the general killchain phases.
    """

    name: str
    killchain: List[List[str]]

    def __init__(self, name, killchain):
        """
        - `name`: Name of ART Campaign
        - `killchain`: 2-Dimensional List killchain[i][j], where
        killchain[i] determines a step in the killchain  and
        killchain[i][j] defines the technique(s) to use in that step.

        Example:
        name = "example_killchain"
        killchain = [
                        ['TA0063', 'TA1042'], # Phase One of Custom Killchain
                        ['TA1068'], # Phase Two of Custom Killchain
                        ...
                    ]
        """
        self.name = name
        self.killchain = killchain
        return NotImplementedError

    def act(self):
        pass
