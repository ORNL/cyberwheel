# CleanRL script for training Cage Challenge 2 agents. CleanRL documentation can be found at https://docs.cleanrl.dev/,
import argparse
import inspect
import os
import random
import subprocess
import time
from distutils.util import strtobool
from pprint import pprint
from pydoc import locate
from typing import List

import gym
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch import multiprocessing
from torch.distributions.categorical import Categorical
from torch.utils.tensorboard import SummaryWriter
from tqdm import tqdm

from cyberwheel.cyberwheel_envs.cyberwheel_dynamic import DynamicCyberwheel


def parse_args():
    # fmt: off
    parser = argparse.ArgumentParser()
    parser.add_argument("--exp-name", type=str, default=os.path.basename(__file__).rstrip(".py"),
        help="the name of this experiment")
    parser.add_argument("--seed", type=int, default=1,
        help="seed of the experiment")
    parser.add_argument("--torch-deterministic", type=lambda x: bool(strtobool(x)), default=True, nargs="?", const=True,
        help="if toggled, `torch.backends.cudnn.deterministic=False`")
    parser.add_argument("--device", type=str, default="cuda",
        help="Choose the device used for optimization. Choose 'cuda', 'cpu', or specify a gpu with 'cuda:0'")
    parser.add_argument("--async-env", type=lambda x: bool(strtobool(x)), default=False, nargs="?", const=True,
        help="if toggled, uses AsyncVectorEnv instead of SyncVectorEnv")
    parser.add_argument('--prod-mode', type=lambda x: bool(strtobool(x)), default=False, nargs='?', const=True,
        help='run the script in production mode and use wandb to log outputs')
    parser.add_argument("--track", type=lambda x: bool(strtobool(x)), default=False, nargs="?", const=True,
        help="if toggled, this experiment will be tracked with Weights and Biases")
    parser.add_argument("--wandb-project-name", type=str, default="Cyberwheel",
        help="the wandb's project name")
    parser.add_argument("--wandb-entity", type=str, default="oeschsec",
        help="the entity (team) of wandb's project")
    parser.add_argument("--capture-video", type=lambda x: bool(strtobool(x)), default=False, nargs="?", const=True,
        help="whether to capture videos of the agent performances (check out `videos` folder)")

    # Algorithm specific arguments
    parser.add_argument("--env-id", type=str, default="cyberwheel",
        help="the id of the environment")
    parser.add_argument("--total-timesteps", type=int, default=500000,
        help="total timesteps of the experiments")
    parser.add_argument("--learning-rate", type=float, default=2.5e-4,
        help="the learning rate of the optimizer")
    parser.add_argument("--num-envs", type=int, default=1,
        help="the number of parallel game environments")
    parser.add_argument("--num-steps", type=int, default=100,
        help="the number of steps to run in each environment per policy rollout")
    parser.add_argument("--anneal-lr", type=lambda x: bool(strtobool(x)), default=True, nargs="?", const=True,
        help="Toggle learning rate annealing for policy and value networks")
    parser.add_argument("--gamma", type=float, default=0.99,
        help="the discount factor gamma")
    parser.add_argument("--gae-lambda", type=float, default=0.95,
        help="the lambda for the general advantage estimation")
    parser.add_argument("--num-minibatches", type=int, default=4,
        help="the number of mini-batches")
    parser.add_argument("--update-epochs", type=int, default=4,
        help="the K epochs to update the policy")
    parser.add_argument("--norm-adv", type=lambda x: bool(strtobool(x)), default=True, nargs="?", const=True,
        help="Toggles advantages normalization")
    parser.add_argument("--clip-coef", type=float, default=0.2,
        help="the surrogate clipping coefficient")
    parser.add_argument("--clip-vloss", type=lambda x: bool(strtobool(x)), default=True, nargs="?", const=True,
        help="Toggles whether or not to use a clipped loss for the value function, as per the paper.")
    parser.add_argument("--ent-coef", type=float, default=0.01,
        help="coefficient of the entropy")
    parser.add_argument("--vf-coef", type=float, default=0.5,
        help="coefficient of the value function")
    parser.add_argument("--max-grad-norm", type=float, default=0.5,
        help="the maximum norm for the gradient clipping")
    parser.add_argument("--target-kl", type=float, default=None,
        help="the target KL divergence threshold")

    # Evaluation Aguments
    parser.add_argument('--max-eval-workers', type=int, default=5,
        help='the maximum number of eval workers (skips evaluation when set to 0)')
    parser.add_argument('--eval-episodes', type=int, default=50,
        help='Number of evaluation episodes to run')
    parser.add_argument("--eval-red-strategy", type=str,
        help="the red agent strategies to evaluate against. Current options: 'killchain_agent' | 'red_recurring' | 'human_teaming'", default="killchain_agent",)
    parser.add_argument("--eval-scenarios", type=str, default="example_config.yaml",
        help="Cyberwheel network to train on.")

    # Cage Arguments
    #parser.add_argument('--baseline',action='store_true')
    parser.add_argument("--red-agent", type=str, default="killchain_agent",
        help="the red agent strategies to train against. Current options: 'killchain_agent' | 'red_recurring'")
    #group = parser.add_mutually_exclusive_group(required=True)
    #group.add_argument("--scenario", type=str,
    #    help="Cage scenario to train on.")
    #group.add_argument("--generate-scenario", action='store_true')
    #group.add_argument("--load-scenario", type=str)

    # network generation args
    parser.add_argument("--network-config", help="Input the network config filename", type=str, default='example_config.yaml')
    parser.add_argument("--decoy-config", help="Input the decoy config filename", type=str, default='decoy_hosts.yaml')
    parser.add_argument("--host-config", help="Input the host config filename", type=str, default='host_definitions.yaml')
    
    # blue agent args
    parser.add_argument("--blue-config", help="Input the blue agent config filename", type=str, default='dynamic_blue_agent.yaml')
    
    # reward calculator args
    parser.add_argument("--min-decoys", help="Minimum number of decoys that should be used", type=int, default=2)
    parser.add_argument("--max-decoys", help="Maximum number of decoys that should be used", type=int, default=3)
    parser.add_argument("--reward-function", help="Which reward function to use. Current options: default | step_detected", type=str, default="default")
    parser.add_argument("--reward-scaling", help="Variable used to increase rewards", type=float, default=10.0)

    # detector args
    parser.add_argument("--detector-config", help="Location of detector config file.", type=str, default="decoys_only.yaml")

    parser.add_argument("--num-hosts", help="num hosts", type=int, default=10)
    args = parser.parse_args()
    args.batch_size = int(args.num_envs * args.num_steps)   # Number of environment steps to performa backprop with
    # args.total_timesteps *= args.num_steps // args.num_hosts
    args.minibatch_size = int(args.batch_size // args.num_minibatches)  # Number of environments steps to perform backprop with in each epoch
    args.num_updates = args.total_timesteps // args.batch_size  # Total number of policy update phases
    args.num_saves = 10    # Number of model saves and evaluations to run throughout training
    args.save_frequency = int(args.num_updates / args.num_saves)    # Number of policy updates between each model save and evaluation

    print(f"Running on network: {args.network_config}")

    return args


def evaluate(
    blue_agent,
    network_config: str,
    decoy_host_file: str,
    host_def_file: str,
    detector_config: str,
    min_decoys=0,
    max_decoys=1,
    blue_reward_scaling=10,
    episodes=20,
    steps=100,
    reward_function="default",
    red_agent="killchain_agent",
    blue_config="dynamic_blue_agent.yaml",
    num_steps=100
):
    """Evaluate 'blue_agent' in the 'scenario' task against the 'red_agent' strategy"""
    # We evaluate on CPU because learning is already happening on GPUs.
    # You can evaluate small architectures on CPU, but if you increase the neural network size,
    # you may need to do fewer evaluations at a time on GPU.
    eval_device = torch.device("cpu")
    env = create_cyberwheel_env(
        network_config,
        decoy_host_file,
        host_def_file,
        detector_config,
        min_decoys=min_decoys,
        max_decoys=max_decoys,
        blue_reward_scaling=blue_reward_scaling,
        reward_function=reward_function,
        red_agent=red_agent,
        blue_config=blue_config,
        num_steps=num_steps
    )
    episode_rewards = []
    total_reward = 0
    # Standard evaluation loop to estimate mean episodic return
    for episode in range(episodes):
        obs, _ = env.reset()
        for step in range(steps):
            obs = torch.Tensor(obs).to(eval_device)
            action, _, _, _ = blue_agent.get_action_and_value(obs)
            obs, rew, done, _, info = env.step(action)
            total_reward += rew
        episode_rewards.append(total_reward)
        total_reward = 0

    episodic_return = float(sum(episode_rewards)) / episodes
    return episodic_return


def run_evals(eval_queue, model, args, globalstep):
    """Evaluate 'model' on tasks listed in 'eval_queue' in a separate process"""
    # TRY NOT TO MODIFY: seeding
    eval_device = torch.device("cpu")

    # This may not be necessary, but we do it in the main training process
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.backends.cudnn.deterministic = args.torch_deterministic
    env_funcs = [
        make_env(
            args.seed, 
            i, 
            args.network_config, 
            args.decoy_config, 
            args.host_config, 
            args.detector_config, 
            min_decoys=args.min_decoys, 
            max_decoys=args.max_decoys, 
            blue_reward_scaling=args.reward_scaling,
            blue_config=args.blue_config
        ) 
        for i in range(1)
    ]

    # Load the agent
    sample_env = gym.vector.SyncVectorEnv(env_funcs)
    eval_agent = Agent(sample_env)
    eval_agent.load_state_dict(torch.load(model, map_location=eval_device))
    eval_agent.eval()

    # Run evaluations in multiprocessing pool
    with multiprocessing.Pool(processes=args.max_eval_workers) as pool:
        # Create a list of arguments for the evaluate_helper function.

        # TODO instead of giving network_config, maybe make the network here and give a deep copy of the network to each env?
        args_list = [
            (
                eval_agent,
                args.network_config,
                args.decoy_config,
                args.host_config,
                args.detector_config,
                args.eval_episodes,
                args.num_steps,
                args.min_decoys,
                args.max_decoys,
                args.reward_scaling,
                args.reward_function,
                args.red_agent,
                args.blue_config,
                args.num_steps
            )
        ]
        # Map the evaluate_helper function to the argument list using the pool
        results = pool.map(evaluate_helper, args_list)
        for result, args in zip(results, args_list):
            _, network_config, decoy_config, _, _, _, _, min_decoys, max_decoys, reward_scaling, reward_function, red_agent, blue_config, num_steps = args
            # Place evaluation results in eval_queue to be read by the main training process.
            # We need to pass these to the main process where wandb is running for logging.
            eval_queue.put(
                (
                    network_config,
                    decoy_config,
                    min_decoys,
                    max_decoys,
                    reward_scaling,
                    reward_function,
                    red_agent,
                    result,
                    globalstep,
                )
            )


def evaluate_helper(args):
    """Unpack arguments for evaluation"""
    agent, network, decoy, host, detector, episodes, steps, min, max, scaling, function, red_agent, blue_config, num_steps = args
    return evaluate(
        agent,
        network,
        decoy,
        host,
        detector,
        episodes=episodes,
        steps=steps,
        min_decoys=min,
        max_decoys=max,
        blue_reward_scaling=scaling,
        reward_function=function,
        red_agent=red_agent,
        blue_config=blue_config,
        num_steps=num_steps
    )


def create_cyberwheel_env(
    network_config: str,
    decoy_host_file: str,
    host_def_file: str,
    detector_config: str,
    min_decoys: int,
    max_decoys: int,
    blue_reward_scaling: float,
    reward_function: str,
    red_agent: str,
    blue_config: str,
    num_steps: int,
):
    """Create a Cyberwheel environment"""
    env = DynamicCyberwheel(
        network_config=network_config,
        decoy_host_file=decoy_host_file,
        host_def_file=host_def_file,
        detector_config=detector_config,
        min_decoys=min_decoys,
        max_decoys=max_decoys,
        blue_reward_scaling=blue_reward_scaling,
        reward_function=reward_function,
        red_agent=red_agent,
        blue_config=blue_config,
        num_steps=num_steps
    )
    return env


def make_env(
    env_id: str,
    rank: int,
    network_config: str,
    decoy_host_file: str,
    host_def_file: str,
    detector_config: str,
    seed: int = 0,
    min_decoys=0,
    max_decoys=1,
    blue_reward_scaling=10,
    reward_function="default",
    red_agent="killchain_agent",
    blue_config="dynamic_blue_agent.yaml",
    num_steps=100
):
    """
    Utility function for multiprocessed env.

    :param env_id: the environment ID
    :param num_env: the number of environments you wish to have in subprocesses
    :param seed: the inital seed for RNG
    :param rank: index of the subprocess
    """

    def _init():
        env = DynamicCyberwheel(
            network_config=network_config,
            decoy_host_file=decoy_host_file,
            host_def_file=host_def_file,
            detector_config=detector_config,
            min_decoys=min_decoys,
            max_decoys=max_decoys,
            blue_reward_scaling=blue_reward_scaling,
            reward_function=reward_function,
            red_agent=red_agent,
            blue_config = blue_config,
            num_steps=num_steps
        )
        env.reset(seed=seed + rank)  # Reset the environment with a specific seed
        env = gym.wrappers.RecordEpisodeStatistics(
            env
        )  # This tracks the rewards of the environment that it wraps. Used for logging
        return env

    return _init


def layer_init(layer, std=np.sqrt(2), bias_const=0.0):
    """Initialise neural network weights using orthogonal initialization. Works well in practice."""
    torch.nn.init.orthogonal_(layer.weight, std)
    torch.nn.init.constant_(layer.bias, bias_const)
    return layer


class Agent(nn.Module):
    """
    The agent class that contains the code for defining the actor and critic networks used by PPO.
    Also includes functions for getting values from the critic and actions from the actor.
    """

    def __init__(self, envs):
        super().__init__()
        # Actor network has an input layer, 2 hidden layers with 64 nodes, and an output layer.
        # Input layer is the size of the observation space and output layer is the size of the action space.
        # Predicts the best action to take at the current state.
        self.actor = nn.Sequential(
            layer_init(
                nn.Linear(int(np.array(envs.single_observation_space.shape).prod()), 64)
            ),
            nn.ReLU(),
            layer_init(nn.Linear(64, 64)),
            nn.ReLU(),
            layer_init(nn.Linear(64, envs.single_action_space.n), std=0.01),
        )

        # Critic network has an input layer, 2 hidden layers with 64 nodes, and an output layer.
        # Input layer is the size of the observation space and output layer has 1 node for the predicted value.
        # Predicts the "value" - the expected cumulative reward from using the actor policy from the current state onward.
        self.critic = nn.Sequential(
            layer_init(
                nn.Linear(int(np.array(envs.single_observation_space.shape).prod()), 64)
            ),
            nn.ReLU(),
            layer_init(nn.Linear(64, 64)),
            nn.ReLU(),
            layer_init(nn.Linear(64, 1), std=1.0),
        )

    def get_value(self, x):
        """Gets the value for a given state x by running x through the critic network"""
        return self.critic(x)

    def get_action_and_value(self, x, action=None):
        """
        Gets the action and value for the current state by running x through the actor and critic respectively.
        Also calculates the log probabilities of the action and the policy's entropy which are used to calculate PPO's training loss.
        """
        logits = self.actor(x)
        probs = Categorical(logits=logits)
        if action is None:
            action = probs.sample()
        return action, probs.log_prob(action), probs.entropy(), self.critic(x)


def main():
    args = parse_args()
    run_name = f"{args.env_id}__{args.exp_name}__{args.seed}__{int(time.time())}"
    if args.track:
        # Initialize Weights and Biases tracking
        import wandb

        wandb.init(
            project=args.wandb_project_name,  # Can be whatever you want
            entity=args.wandb_entity,  # Should be oeschsec or a subgroup of that account
            sync_tensorboard=True,  # Data logged to the tensorboard SummaryWriter will be sent to W&B
            config=vars(args),  # Saves args as the run's configuration
            name=run_name,  # Unique run name
            monitor_gym=False,  # Does not attempt to render any episodes (CAGE doesn't support it)
            save_code=False,  # Don't save any FOUO code
        )
    writer = SummaryWriter(f"runs/{run_name}")  # Logs data to tensorboard and W&B
    writer.add_text(
        "hyperparameters",
        "|param|value|\n|-|-|\n%s"
        % ("\n".join([f"|{key}|{value}|" for key, value in vars(args).items()])),
    )

    # TRY NOT TO MODIFY: seeding
    # We need to seed all sources of randomness for reproducibility. If you run the same seed you should get the same results.
    # This of course requires the environment to be seeded, which we don't do for CAGE, so it won't work for us.
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.backends.cudnn.deterministic = args.torch_deterministic

    # Use a GPU if it's available. You can choose a specific GPU (for example, our 3rd GPU) by setting --device to "cuda:2"
    # device = torch.device(args.device if torch.cuda.is_available() else "cpu")
    device = args.device
    print(f"Using device {device}")

    # Environment setup
    # The AsyncVectorEnv creates multiple environments running in separate processes to collect experience.
    # The more environments you use, the faster you can train, though there are diminishing returns. We set num_envs to 128.
    # However this also increases batch size and as a result, VRAM usage.
    # For large neural networks you may need to use fewer environments.
    # NOTE: For debugging, you can change AsyncVectorENv to SyncVectorEnv (and reduce num_envs) to get more helpful stack traces.

    # TODO Load network from yaml here?
    env_funcs = [
        make_env(
            args.seed,
            i,
            args.network_config,
            args.decoy_config,
            args.host_config,
            args.detector_config,
            min_decoys=args.min_decoys,
            max_decoys=args.max_decoys,
            blue_reward_scaling=args.reward_scaling,
            reward_function=args.reward_function,
            red_agent=args.red_agent,
            num_steps=args.num_steps
        )
        for i in range(args.num_envs)
    ]
    envs = (
        gym.vector.AsyncVectorEnv(env_funcs)
        if args.async_env
        else gym.vector.SyncVectorEnv(env_funcs)
    )
    assert isinstance(
        envs.single_action_space, gym.spaces.Discrete
    ), "only discrete action space is supported"

    # Evaluation setup
    eval_queue = multiprocessing.SimpleQueue()
    eval_processes = []

    # Create agent and optimizer
    agent = Agent(envs).to(device)
    optimizer = optim.Adam(agent.parameters(), lr=args.learning_rate, eps=1e-5)

    # ALGO Logic: Storage setup
    obs = torch.zeros(
        (args.num_steps, args.num_envs) + envs.single_observation_space.shape
    ).to(device)
    # print(envs.single_observation_space.shape)
    actions = torch.zeros(
        (args.num_steps, args.num_envs) + envs.single_action_space.shape
    ).to(device)
    logprobs = torch.zeros((args.num_steps, args.num_envs)).to(device)
    rewards = torch.zeros((args.num_steps, args.num_envs)).to(device)
    dones = torch.zeros((args.num_steps, args.num_envs)).to(device)
    values = torch.zeros((args.num_steps, args.num_envs)).to(device)
    step_rewards = torch.zeros((args.num_steps, args.num_envs))

    # TRY NOT TO MODIFY: start the game

    global_step = 0
    start_time = time.time()
    resets = np.array(envs.reset()[0])
    next_obs = torch.Tensor(resets).to(device)
    next_done = torch.zeros(args.num_envs).to(device)
    num_updates = args.total_timesteps // args.batch_size
    # print(list(np.zeros(envs.single_observation_space.shape)))

    for update in range(1, num_updates + 1):
        # We need to manually reset the environment for CAGE. Most environments don't require this.
        # NOTE: When a curriculum is being used, this will automatically change the environment task.
        resets = np.array(envs.reset()[0])
        next_obs = torch.Tensor(resets).to(device)

        # Annealing the rate if instructed to do so.
        if args.anneal_lr:
            # Decreases the learning rate from args.lr to 0 over the course of training.
            frac = 1.0 - (update - 1.0) / num_updates
            lrnow = frac * args.learning_rate
            optimizer.param_groups[0]["lr"] = lrnow

        # Run an episode in each environment. This loop collects experience which is later used for optimization.
        episode_start = time.time_ns()
        for step in range(0, args.num_steps):
            global_step += 1 * args.num_envs
            obs[step] = next_obs
            dones[step] = next_done

            # ALGO LOGIC: action logic
            # Select an action using the current policy and get a value estimate
            with torch.no_grad():
                action, logprob, _, value = agent.get_action_and_value(next_obs)
                values[step] = value.flatten()

            actions[step] = action
            logprobs[step] = logprob
            # TRY NOT TO MODIFY: execute the game and log data.
            # Execute the selected action in the environment to collect experience for training.
            # action_list = [action]
            # print(action.cpu().numpy())
            temp_action = action.cpu().numpy()
            next_obs, reward, done, _, info = envs.step(temp_action)
            rewards[step] = torch.tensor(reward).to(device).view(-1)
            next_obs, next_done = torch.Tensor(next_obs).to(device), torch.Tensor(
                done
            ).to(device)
        end_time = time.time_ns()
        episode_time = (end_time - episode_start) / (10**9)
        # Calculate and log the mean reward for this episode.
        mean_rew = rewards.sum(axis=0).mean()
        print(f"global_step={global_step}, episodic_return={mean_rew}")
        writer.add_scalar("charts/episodic_return", mean_rew, global_step)
        writer.add_scalar(
            f"evaluation/episodic_runtime",
            episode_time,
            global_step,
        )

        # bootstrap value if not done
        # Calculate advantages used to optimize the policy and returns which are compared to values to optimize the critic.
        with torch.no_grad():
            next_value = agent.get_value(next_obs).reshape(1, -1)
            advantages = torch.zeros_like(rewards).to(device)
            lastgaelam = 0
            for t in reversed(range(args.num_steps)):
                if t == args.num_steps - 1:
                    nextnonterminal = 1.0 - next_done
                    nextvalues = next_value
                else:
                    nextnonterminal = 1.0 - dones[t + 1]
                    nextvalues = values[t + 1]
                delta = (
                    rewards[t] + args.gamma * nextvalues * nextnonterminal - values[t]
                )
                advantages[t] = lastgaelam = (
                    delta + args.gamma * args.gae_lambda * nextnonterminal * lastgaelam
                )
            returns = advantages + values

        # flatten the batch
        b_obs = obs.reshape((-1,) + envs.single_observation_space.shape)
        b_logprobs = logprobs.reshape(-1)
        b_actions = actions.reshape((-1,) + envs.single_action_space.shape)
        b_advantages = advantages.reshape(-1)
        b_returns = returns.reshape(-1)
        b_values = values.reshape(-1)

        # Optimizing the policy and value network
        b_inds = np.arange(args.batch_size)
        clipfracs = []
        # Iterate over multiple epochs which each update the policy using all of the batch data
        for epoch in range(args.update_epochs):
            np.random.shuffle(b_inds)

            # For each epoch, split the batch into minibatches for smaller updates
            for start in range(0, args.batch_size, args.minibatch_size):
                end = start + args.minibatch_size
                mb_inds = b_inds[start:end]

                _, newlogprob, entropy, newvalue = agent.get_action_and_value(
                    b_obs[mb_inds], b_actions.long()[mb_inds]
                )
                logratio = newlogprob - b_logprobs[mb_inds]
                ratio = logratio.exp()

                # Calculate the difference between the old policy and the new policy to limit the size of the update using args.clip_coef.
                with torch.no_grad():
                    # calculate approx_kl http://joschu.net/blog/kl-approx.html
                    old_approx_kl = (-logratio).mean()
                    approx_kl = ((ratio - 1) - logratio).mean()
                    clipfracs += [
                        ((ratio - 1.0).abs() > args.clip_coef).float().mean().item()
                    ]

                mb_advantages = b_advantages[mb_inds]
                if args.norm_adv:
                    mb_advantages = (mb_advantages - mb_advantages.mean()) / (
                        mb_advantages.std() + 1e-8
                    )

                # Policy loss using PPO's ration clipping
                pg_loss1 = -mb_advantages * ratio
                pg_loss2 = -mb_advantages * torch.clamp(
                    ratio, 1 - args.clip_coef, 1 + args.clip_coef
                )
                pg_loss = torch.max(pg_loss1, pg_loss2).mean()

                # Value loss
                newvalue = newvalue.view(-1)
                # Calculate the MSE loss between the returns and the value predictions of the critic
                # Clipping V loss is often not necessary and arguably worse in practice
                if args.clip_vloss:
                    v_loss_unclipped = (newvalue - b_returns[mb_inds]) ** 2
                    v_clipped = b_values[mb_inds] + torch.clamp(
                        newvalue - b_values[mb_inds],
                        -args.clip_coef,
                        args.clip_coef,
                    )
                    v_loss_clipped = (v_clipped - b_returns[mb_inds]) ** 2
                    v_loss_max = torch.max(v_loss_unclipped, v_loss_clipped)
                    v_loss = 0.5 * v_loss_max.mean()
                else:
                    v_loss = 0.5 * ((newvalue - b_returns[mb_inds]) ** 2).mean()

                # Add an entropy bonus to the loss
                entropy_loss = entropy.mean()
                loss = pg_loss - args.ent_coef * entropy_loss + v_loss * args.vf_coef

                # Backpropagation
                optimizer.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(agent.parameters(), args.max_grad_norm)
                optimizer.step()

            if args.target_kl is not None:
                if approx_kl > args.target_kl:
                    break

        y_pred, y_true = b_values.cpu().numpy(), b_returns.cpu().numpy()
        var_y = np.var(y_true)
        explained_var = np.nan if var_y == 0 else 1 - np.var(y_true - y_pred) / var_y

        # Infrequently save the model and evaluate the agent
        if (update - 1) % args.save_frequency == 0:
            start_eval = time.time()

            # Save the model
            if not os.path.exists(f"models/{run_name}"):
                os.makedirs(f"models/{run_name}")
            torch.save(agent.state_dict(), f"models/{run_name}/agent.pt")
            torch.save(agent.state_dict(), f"models/{run_name}/{global_step}.pt")
            if args.track:
                wandb.save(
                    f"models/{run_name}/agent.pt",
                    base_path=f"models/{run_name}",
                    policy="now",
                )

            # Run evaluation
            print("Evaluating Agent")
            run_evals(
                eval_queue, f"models/{run_name}/{global_step}.pt", args, global_step
            )

            # Log eval results
            while not eval_queue.empty():
                (
                    eval_network_config,
                    eval_decoy_config,
                    eval_min_decoys,
                    eval_max_decoys,
                    eval_reward_scaling,
                    eval_reward_function,
                    eval_red_agent,
                    eval_return,
                    eval_step,
                ) = eval_queue.get()
                writer.add_scalar(
                    f"evaluation/{eval_network_config.split('.')[0]}_{eval_decoy_config}_{eval_reward_scaling}|{eval_min_decoys}-{eval_max_decoys}_{eval_reward_function}reward__{eval_red_agent}_episodic_return",
                    eval_return,
                    eval_step,
                )
            writer.add_scalar(
                "charts/eval_time", int(time.time() - start_eval), global_step
            )

        # TRY NOT TO MODIFY: record rewards for plotting purposes
        writer.add_scalar(
            "charts/learning_rate", optimizer.param_groups[0]["lr"], global_step
        )
        writer.add_scalar("losses/value_loss", v_loss.item(), global_step)
        writer.add_scalar("losses/policy_loss", pg_loss.item(), global_step)
        writer.add_scalar("losses/entropy", entropy_loss.item(), global_step)
        writer.add_scalar("losses/old_approx_kl", old_approx_kl.item(), global_step)
        writer.add_scalar("losses/approx_kl", approx_kl.item(), global_step)
        writer.add_scalar("losses/clipfrac", np.mean(clipfracs), global_step)
        writer.add_scalar("losses/explained_variance", explained_var, global_step)
        print("SPS:", int(global_step / (time.time() - start_time)))
        writer.add_scalar(
            "charts/SPS", int(global_step / (time.time() - start_time)), global_step
        )

    # Allow final evaluations to finish and record results
    processes_running = True
    while processes_running:
        # Check if any processes are running
        processes_running = False
        for process in eval_processes:
            if process.is_alive():
                processes_running = True

        # Process evaluation results
        while not eval_queue.empty():
            (
                eval_network_config,
                eval_decoy_config,
                eval_min,
                eval_max,
                eval_scaling,
                eval_reward,
                eval_return,
                eval_step,
            ) = eval_queue.get()
            writer.add_scalar(
                f"evaluation/{eval_network_config.split('.')[0]}_{eval_decoy_config}_{eval_scaling}|{eval_min}-{eval_max}_{eval_reward}rewardepisodic_return",
                eval_return,
                eval_step,
            )

    envs.close()
    writer.close()


if __name__ == "__main__":
    multiprocessing.set_start_method("spawn")
    main()
