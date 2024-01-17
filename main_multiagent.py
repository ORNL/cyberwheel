'''
In PettingZoo, independent multi-agent mode refers to a mode where each agent acts independently of the others. 
In this mode, each agent has its own observation space and action space, and makes decisions based on its own observations, 
without any direct communication or coordination with other agents.

https://github.com/ray-project/ray/blob/master/rllib/examples/multi_agent_independent_learning.py#L26
'''
from pettingzoo.test import parallel_api_test
from cyberwheel_multiagent import MultiagentCyberwheel

import argparse
from ray import air, tune
from ray.tune.registry import register_env
from ray.rllib.algorithms.ppo import PPOConfig
from ray.rllib.env.wrappers.pettingzoo_env import ParallelPettingZooEnv # RLLib Wrapper for Parallel Petting Zoo Environments
from ray.rllib.algorithms.callbacks import DefaultCallbacks
from ray.rllib.algorithms.ppo import PPO
from ray.tune import CLIReporter
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument(
    "--num-gpus",
    type=int,
    default=1,
    help="Number of GPUs to use for training.",
)
parser.add_argument(
    "--as-test",
    action="store_true",
    help="Whether this script should be run as a test: Only one episode will be "
    "sampled.",
)

class MyCallbacks(DefaultCallbacks):
    def on_train_result(self, *, algorithm, result: dict, **kwargs):
        result["custom_metrics"]["policy_reward_mean"] = {
            "blue_agent": result["policy_reward_mean"].get("blue_agent", np.nan),
            "red_agent": result["policy_reward_mean"].get("red_agent", np.nan),
        }

if __name__ == "__main__":
    pzenv = MultiagentCyberwheel()

    # Test to verify the environment is compliant with the API
    parallel_api_test(pzenv, num_cycles=1_000_000)

    args = parser.parse_args()

    def env_creator(args):
        return ParallelPettingZooEnv(pzenv)

    env = env_creator({})
    register_env("cyberwheel", env_creator)

    config = (
        PPOConfig()
        .environment("cyberwheel")
        .resources(num_gpus=args.num_gpus)
        .rollouts(num_rollout_workers=2)
        .multi_agent(
            policies=env.get_agent_ids(),
            policy_mapping_fn=(lambda agent_id, *args, **kwargs: agent_id),
        )
        .callbacks(MyCallbacks)
    )

    if args.as_test:
        # Only a compilation test of running waterworld / independent learning.
        stop = {"training_iteration": 1}
    else:
        stop = {"episodes_total": 60000}

    trainer = PPO(config=config)

    # Number of training iterations
    N_ITERATIONS = 10

    for _ in range(N_ITERATIONS):
        result = trainer.train()

        # Print the mean reward for each agent
        for agent, reward in result["policy_reward_mean"].items():
            print(f"Mean reward for {agent}: {reward}")
        
        print("Mean episode length: " + str(result["episode_len_mean"]))

    # tune.Tuner(
    #     "PPO",
    #     run_config=air.RunConfig(
    #         stop=stop,
    #         checkpoint_config=air.CheckpointConfig(
    #             checkpoint_frequency=1000,
    #         ),
    #     progress_reporter=CLIReporter(
    #         metric_columns={
    #             "training_iteration": "training_iteration",
    #             "time_total_s": "time_total_s",
    #             "timesteps_total": "timesteps",
    #             "episodes_this_iter": "episodes_trained",
    #             "custom_metrics/policy_reward_mean/blue_agent": "m_reward_blue",
    #             "custom_metrics/policy_reward_mean/red_agent": "m_reward_red",
    #             "episode_reward_mean": "mean_reward_sum",
    #         },
    #         sort_by_metric=True,
    #     ),
    #     ),
    #     param_space=config,
    # ).fit()