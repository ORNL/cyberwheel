import yaml
import importlib

from pathlib import PosixPath
from typing_extensions import Self, Tuple, Type

from cyberwheel.red_actions.red_base import RedActionResults
from cyberwheel.red_agents import ARTAgent
from cyberwheel.red_agents.red_agent_base import RedAgentResult
from cyberwheel.network.network_base import Network, Host
from cyberwheel.red_actions.technique import Technique
from cyberwheel.red_actions import art_techniques
from cyberwheel.reward import RewardMap


class ARTCampaign(ARTAgent):
    """
    Class defining an ART Campaign. Where the ART Agent performs logic checking to find valid
    ART Techniques to use on a host, ART Campaigns are defined with ART Techniques in the killchain.
    These are also
    """

    def __init__(
        self,
        network: Network,
        args
    ):
        self.args = args

        super().__init__(
            network,
            args
        )
    
    def from_yaml(self) -> None:
        with open(self.config, "r") as f:
            config = yaml.safe_load(f)
        self.entry_host: str = config["entry_host"]
        self.current_host : Host = self.network.hosts[self.entry_host] if self.entry_host.lower() != "random" else self.network.get_random_user_host()
        self.leader = config["leader"]
        self.leader_host = self.network.hosts[config["leader"]] if self.leader.lower() != "random" else self.network.get_random_server_host()
        sm = importlib.import_module("cyberwheel.red_agents.strategies")
        self.strategy = getattr(sm, config['strategy'])

        self.killchain = []
        self.reward = {}

        for t in config["campaign"]:
            technique_name = t["technique_name"]
            atomic_test_guid = t["atomic_test_guid"]
            technique_class = getattr(art_techniques, technique_name)
            atomic_test_class = technique_class().get_atomic_test(atomic_test_guid)
            self.killchain.append({"technique": technique_class, "atomic_test": atomic_test_class})
            self.reward[technique_class().name] = (
                -float(t["reward"]["immediate"]),
                -float(t["reward"]["recurring"]) if "recurring" in t["reward"] else 0.0,
            )
        if config["lateral_movement_technique"] != None:
            self.lateral_movement_technique = getattr(
                art_techniques, config["lateral_movement_technique"]
            )
            self.lateral_movement_atomic_test = self.lateral_movement_technique().get_atomic_test(
                config["lateral_movement_atomic_test"]
            )
            self.lateral_movement_reward = config["lateral_movement_reward"]
        else: # TODO: Lateral Movement not functional yet
            self.lateral_movement_technique = None
            self.lateral_movement_atomic_test = None
            self.lateral_movement_reward = 0.0

    def run_action(self, target_host: Host) -> Tuple[RedActionResults, Type[Technique]]:
        step = self.history.hosts[target_host.name].get_next_step()
        self.do_lateral_movement = False
        if step > len(self.killchain) - 1:
            step = len(self.killchain) - 1

        if self.current_host.name == target_host.name:
            technique_class = self.killchain[step]["technique"]
            atomic_test = self.killchain[step]["atomic_test"]
        else:  # Will do lateral movement to get onto other host before continuing
            technique_class = self.lateral_movement_technique
            atomic_test = self.lateral_movement_atomic_test
            self.do_lateral_movement = True

        technique = technique_class()
        mitre_id = technique.mitre_id
        technique_name = technique.name

        action_results = RedActionResults(self.current_host, target_host)
        action_results.modify_alert(dst=target_host, src=self.current_host)

        action_results.add_successful_action()

        processes = []
        for dep in atomic_test.dependencies:
            processes.extend(dep.get_prerequisite_command)
            processes.extend(dep.prerequisite_command)
        if atomic_test.executor != None:
            processes.extend(atomic_test.executor.command)
            processes.extend(atomic_test.executor.cleanup_command)

        for p in processes:
            target_host.run_command(atomic_test.executor, p, "root")
        action_results.add_metadata(
            target_host.name,
            {
                "commands": processes,
                "mitre_id": mitre_id,
                "technique": technique_name,
            },
        )
        return action_results, technique_class

    def act(self, policy_action=None) -> RedAgentResult:
        """
        This defines the red agent's action at each step of the simulation.
        It will
            *   handle any newly added hosts
            *   Select the next target
            *   Run an action on the target
            *   Handle any additional metadata and update history
        """
        self.handle_network_change()

        target_host = self.select_next_target()
        source_host = self.current_host
        action_results, action = self.run_action(target_host)
        action_obj = action()
        success = action_results.attack_success
        if success:
            if not self.do_lateral_movement:
                self.history.hosts[target_host.name].update_killchain_step()
            for h_name in action_results.metadata.keys():
                self.add_host_info(action_results.metadata)
            if "impact" in action_obj.kill_chain_phases:  # If KCP was Impact
                self.history.hosts[target_host.name].impacted = True
                if self.history.hosts[target_host.name].type == "Server":
                    self.unimpacted_servers.remove(target_host.name)

        #print(f"{action_obj.name} - from {source_host.name} to {target_host.name}")
        self.history.update_step(action, action_results)
        return RedAgentResult(
            action, 
            source_host, 
            target_host, 
            success,
            action_results=action_results
        )  # Returns what ARTAgent act() should, probably. Or the observation space?

    @classmethod
    def create_campaign_from_yaml(
        cls, campaign_config: PosixPath, network: Network
    ) -> Self:
        reward = {}
        campaign = []

        # Load the YAML config file
        with open(campaign_config, "r") as yaml_file:
            config = yaml.safe_load(yaml_file)

        campaign_name = config["name"]
        entry_host_name = config["entry_host"]
        if entry_host_name == None:
            entry_host_name = network.get_random_user_host().name
        leader_name = config["leader"]
        strategy = config["strategy"]

        for t in config["campaign"]:
            technique_name = t["technique_name"]
            atomic_test_guid = t["atomic_test_guid"]
            technique_class = getattr(art_techniques, technique_name)
            atomic_test = technique_class().get_atomic_test(atomic_test_guid)
            campaign.append({"technique": technique_class, "atomic_test": atomic_test})
            reward[technique_class().name] = (
                -float(t["reward"]["immediate"]),
                -float(t["reward"]["recurring"]) if "recurring" in t["reward"] else 0.0,
            )
        if config["lateral_movement_technique"] != None:
            lateral_movement_technique = getattr(
                art_techniques, config["lateral_movement_technique"]
            )
            lateral_movement_atomic_test = lateral_movement_technique().get_atomic_test(
                config["lateral_movement_atomic_test"]
            )
            lateral_movement_reward = config["lateral_movement_reward"]
        else:
            lateral_movement_technique = None
            lateral_movement_atomic_test = None
            lateral_movement_reward = 0.0

        return ARTCampaign(
            name=campaign_name,
            entry_host_name=entry_host_name,
            leader_host_name=leader_name,
            strategy=strategy,
            campaign=campaign,
            lateral_movement_technique=lateral_movement_technique,
            lateral_movement_atomic_test=lateral_movement_atomic_test,
            lateral_movement_reward=lateral_movement_reward,
            reward=reward,
            network=network,
        )

    def get_reward_map(self) -> RewardMap:
        """
        Get the reward mapping for the red campaign. This is defined in the campaign YAML.
        """
        return self.reward
