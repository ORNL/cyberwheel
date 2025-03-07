import torch
import random
import gymnasium as gym
import time
import os
import importlib
import numpy as np

from copy import deepcopy
from torch.utils.tensorboard import SummaryWriter
from torch import optim, nn
from importlib.resources import files

from cyberwheel.utils import RLAgent, get_service_map
from cyberwheel.utils.set_seed import set_seed
from cyberwheel.network.network_base import Network

class Trainer:
    def __init__(self, args):
        self.args = args
        m = importlib.import_module("cyberwheel.cyberwheel_envs")
        self.env = getattr(m, args.environment)
        self.deterministic = os.getenv("CYBERWHEEL_DETERMINISTIC", "False").lower() in ('true', '1', 't')
        self.args.deterministic = self.deterministic
        self.seed = 0
    def make_env(self, rank, evaluation: bool = False):
        """
        Utility function for multiprocessed env.

        :param env_id: the environment ID
        :param num_env: the number of environments you wish to have in subprocesses
        :param rank: index of the subprocess
        """

        def _init():
            if evaluation:
                config_path = files("cyberwheel.data.configs.network").joinpath(self.args.network_config)
                env = self.env(self.args, network=Network.create_network_from_yaml(config_path), evaluation=True)
            else:
                env = self.env(self.args, network=self.networks[rank], evaluation=False)
            self.max_action_space_size = env.max_action_space_size
            env.reset()
            env = gym.wrappers.RecordEpisodeStatistics(
                env
            )  # This tracks the rewards of the environment that it wraps. Used for logging
            return env

        return _init
    
    def get_action_mask(self, action_space_size, action_masks):
        action_masks[:action_space_size] = True # Valid actions
        action_masks[action_space_size:] = False # Invalid actions
        return action_masks
    
    def evaluate(self, agent, env):
        """Evaluate 'agent'"""
        # We evaluate on CPU because learning is already happening on GPUs.
        # You can evaluate small architectures on CPU, but if you increase the neural network size,
        # you may need to do fewer evaluations at a time on GPU.
        eval_device = torch.device("cpu")
        #env = self.env(self.args, )
        episode_rewards = []
        action_masks = torch.zeros(self.max_action_space_size, dtype=torch.bool).to(eval_device)
        total_reward = 0
        # Standard evaluation loop to estimate mean episodic return
        for episode in range(self.args.eval_episodes):
            #episode_start_time = time.time()
            obs, _ = env.reset()
            for step in range(self.args.num_steps):
                obs = torch.Tensor(obs).to(eval_device)

                action_masks = self.get_action_mask(env.envs[0].unwrapped.rl_agent.action_space._action_space_size, action_masks)

                action, _, _, _ = agent.get_action_and_value(
                    obs, action_mask=action_masks
                )
                eval_step_start_time = time.time()
                obs, rew, done, _, info = env.step(action)
                #print(f"Evaluation step took: \t\t{time.time() - eval_step_start_time}")
                total_reward += rew
            episode_rewards.append(total_reward)
            total_reward = 0
            #episode_time = time.time() - episode_start_time
            #print(f"Evaluation ep took: \t\t{episode_time}")

        episodic_return = float(sum(episode_rewards)) / self.args.eval_episodes
        return episodic_return
    
    def run_evals(self, model, globalstep):
        """Evaluate 'model' on tasks listed in 'eval_queue' in a separate process"""
        eval_device = torch.device("cpu")

        env_funcs = [self.make_env(i, evaluation=True) for i in range(1)]

        # Load the agent
        sample_env = gym.vector.SyncVectorEnv(env_funcs)
        eval_agent = RLAgent(sample_env)
        model = torch.load(model, map_location=eval_device)
        eval_agent.load_state_dict(model)
        eval_agent.eval()
        # Evaluate the agent
        result = self.evaluate(eval_agent, sample_env)
        # Store evaluation parameters and results
        return (
            self.args.network_config,
            self.args.decoy_config,
            self.args.reward_function,
            self.args.red_agent,
            result,
            globalstep,
        )
    
    def wandb_setup(self):
        # Initialize Weights and Biases tracking
        import wandb

        wandb.init(
            project=self.args.wandb_project_name,  # Can be whatever you want
            entity=self.args.wandb_entity,
            sync_tensorboard=True,  # Data logged to the tensorboard SummaryWriter will be sent to W&B
            config=vars(self.args),  # Saves args as the run's configuration
            name=self.args.experiment_name,  # Unique run name
            monitor_gym=False,  # Does not attempt to render any episodes
            save_code=False,
        )

    def configure_training(self):
        self.writer = SummaryWriter(
            files("cyberwheel.data.runs").joinpath(self.args.experiment_name)
        )  # Logs data to tensorboard and W&B
        self.writer.add_text(
            "hyperparameters",
            "|param|value|\n|-|-|\n%s"
            % ("\n".join([f"|{key}|{value}|" for key, value in vars(self.args).items()])),
        )
        # Seeding
        if self.deterministic:
            set_seed(self.seed)
            torch.backends.cudnn.deterministic = True
        else:
            torch.backends.cudnn.deterministic = False
            #torch.set_num_threads(1)

        # Use a GPU if available. You can choose a specific GPU with CUDA, for example by setting --device to "cuda:0"
        # Defaults to 'cpu'
        self.device = self.args.device
        print(f"Using device {self.device}")

        # Environment setup

        # Load network from yaml here
        network_config = files("cyberwheel.data.configs.network").joinpath(
            self.args.network_config
        )

        print(f"Building network: {self.args.network_config} ...")

        network = Network.create_network_from_yaml(network_config)
        self.networks = [deepcopy(network) for i in range(self.args.num_envs)]

        print("Mapping attack validity to hosts...", end=" ")
        self.args.service_mapping = get_service_map(network)
        print("done")

        print("Defining environment(s) and beginning training:", end="\n\n")

        env_funcs = [self.make_env(i) for i in range(self.args.num_envs)]

        self.envs = (
            gym.vector.AsyncVectorEnv(env_funcs)
            if self.args.async_env
            else gym.vector.SyncVectorEnv(env_funcs)
        )

        assert isinstance(
            self.envs.single_action_space, gym.spaces.Discrete
        ), "only discrete action space is supported"

        # Create agent and optimizer

        self.agent = RLAgent(self.envs).to(self.device)

        # Load model from models/ directory

        self.optimizer = optim.Adam(self.agent.parameters(), lr=self.args.learning_rate, eps=1e-5)

        # ALGO Logic: Storage setup
        self.obs = torch.zeros(
            (self.args.num_steps, self.args.num_envs) + self.envs.single_observation_space.shape
        ).to(self.device)
        self.actions = torch.zeros(
            (self.args.num_steps, self.args.num_envs) + self.envs.single_action_space.shape
        ).to(self.device)
        self.logprobs = torch.zeros((self.args.num_steps, self.args.num_envs)).to(self.device)
        self.rewards = torch.zeros((self.args.num_steps, self.args.num_envs)).to(self.device)
        self.dones = torch.zeros((self.args.num_steps, self.args.num_envs)).to(self.device)
        self.values = torch.zeros((self.args.num_steps, self.args.num_envs)).to(self.device)
        self.step_rewards = torch.zeros((self.args.num_steps, self.args.num_envs))
        self.action_masks = torch.zeros(
            (self.args.num_steps, self.args.num_envs, self.max_action_space_size), dtype=torch.bool
        ).to(self.device)
        self.global_step = 0
        self.start_time = time.time()
        self.resets = np.array(self.envs.reset(seed=[self.seed + i for i in range(self.args.num_envs)])[0])
        self.next_obs = torch.Tensor(self.resets).to(self.device)
        self.next_done = torch.zeros(self.args.num_envs).to(self.device)

    def train(self, update):
        # Annealing the rate if instructed to do so.
        if self.args.anneal_lr:
            # Decreases the learning rate from args.lr to 0 over the course of training.
            frac = 1.0 - (update - 1.0) / self.args.num_updates
            lrnow = frac * self.args.learning_rate
            self.optimizer.param_groups[0]["lr"] = lrnow

        # Run an episode in each environment. This loop collects experience which is later used for optimization.
        episode_start = time.time_ns()
        for step in range(0, self.args.num_steps):

            if self.deterministic:
                set_seed(self.seed)
            self.seed += self.args.num_envs
            
            if isinstance(self.envs, gym.vector.AsyncVectorEnv):
                action_space_sizes = self.envs.call("rl_agent_action_space_size")
            else:
                action_space_sizes = [
                    env.unwrapped.rl_agent.action_space._action_space_size for env in self.envs.envs
                ]

            for i, action_space_size in enumerate(action_space_sizes):
                self.action_masks[step][i] = self.get_action_mask(action_space_size, self.action_masks[step][i])

            self.global_step += 1 * self.args.num_envs
            self.obs[step] = self.next_obs
            self.dones[step] = self.next_done

            # ALGO LOGIC: action logic
            # Select an action using the current policy and get a value estimate
            with torch.no_grad():
                action, logprob, _, value = self.agent.get_action_and_value(
                    self.next_obs, action_mask=self.action_masks[step]
                )
                self.values[step] = value.flatten()

            self.actions[step] = action
            self.logprobs[step] = logprob
            # TRY NOT TO MODIFY: execute the game and log data.
            # Execute the selected action in the environment to collect experience for training.
            temp_action = action.cpu().numpy()
            #train_step_start_time = time.time()
            self.next_obs, reward, done, _, info = self.envs.step(temp_action)
            #print(f"Training step took: \t\t{time.time() - train_step_start_time}")
            self.rewards[step] = torch.tensor(reward).to(self.device).view(-1)
            self.next_obs, self.next_done = torch.Tensor(self.next_obs).to(self.device), torch.Tensor(
                done
            ).to(self.device)
        end_time = time.time_ns()
        episode_time = (end_time - episode_start) / (10**9)
        #print(f"Training ep took: \t\t{episode_time}")

        # Calculate and log the mean reward for this episode.
        #print(self.rewards.sum(axis=0))
        #print(self.rewards.sum(axis=0).mean())
        mean_rew = self.rewards.sum(axis=0).mean()
        print(f"global_step={self.global_step}, episodic_return={mean_rew}")
        self.writer.add_scalar("charts/episodic_return", mean_rew, self.global_step)
        self.writer.add_scalar(
            f"evaluation/episodic_runtime",
            episode_time,
            self.global_step,
        )
        


        # bootstrap value if not done
        # Calculate advantages used to optimize the policy and returns which are compared to values to optimize the critic.
        with torch.no_grad():
            next_value = self.agent.get_value(self.next_obs).reshape(1, -1)
            advantages = torch.zeros_like(self.rewards).to(self.device)
            lastgaelam = 0
            for t in reversed(range(self.args.num_steps)):
                if t == self.args.num_steps - 1:
                    nextnonterminal = 1.0 - self.next_done
                    nextvalues = next_value
                else:
                    nextnonterminal = 1.0 - self.dones[t + 1]
                    nextvalues = self.values[t + 1]
                delta = (
                    self.rewards[t] + self.args.gamma * nextvalues * nextnonterminal - self.values[t]
                )
                advantages[t] = lastgaelam = (
                    delta + self.args.gamma * self.args.gae_lambda * nextnonterminal * lastgaelam
                )
            returns = advantages + self.values

        # flatten the batch
        b_obs = self.obs.reshape((-1,) + self.envs.single_observation_space.shape)
        b_logprobs = self.logprobs.reshape(-1)
        b_actions = self.actions.reshape((-1,) + self.envs.single_action_space.shape)
        b_advantages = advantages.reshape(-1)
        b_returns = returns.reshape(-1)
        b_values = self.values.reshape(-1)
        b_action_masks = self.action_masks.reshape(-1, self.action_masks.shape[-1])

        # Optimizing the policy and value network
        b_inds = np.arange(self.args.batch_size)
        clipfracs = []
        # Iterate over multiple epochs which each update the policy using all of the batch data
        for epoch in range(self.args.update_epochs):
            np.random.shuffle(b_inds)

            # For each epoch, split the batch into minibatches for smaller updates
            for start in range(0, self.args.batch_size, self.args.minibatch_size):
                end = start + self.args.minibatch_size
                mb_inds = b_inds[start:end]

                _, newlogprob, entropy, newvalue = self.agent.get_action_and_value(
                    b_obs[mb_inds],
                    b_actions.long()[mb_inds],
                    action_mask=b_action_masks[mb_inds],
                )
                logratio = newlogprob - b_logprobs[mb_inds]
                ratio = logratio.exp()

                # Calculate the difference between the old policy and the new policy to limit the size of the update using args.clip_coef.
                with torch.no_grad():
                    # calculate approx_kl http://joschu.net/blog/kl-approx.html
                    old_approx_kl = (-logratio).mean()
                    approx_kl = ((ratio - 1) - logratio).mean()
                    clipfracs += [
                        ((ratio - 1.0).abs() > self.args.clip_coef).float().mean().item()
                    ]

                mb_advantages = b_advantages[mb_inds]
                if self.args.norm_adv:
                    mb_advantages = (mb_advantages - mb_advantages.mean()) / (
                        mb_advantages.std() + 1e-8
                    )

                # Policy loss using PPO's ration clipping
                pg_loss1 = -mb_advantages * ratio
                pg_loss2 = -mb_advantages * torch.clamp(
                    ratio, 1 - self.args.clip_coef, 1 + self.args.clip_coef
                )
                pg_loss = torch.max(pg_loss1, pg_loss2).mean()

                # Value loss
                newvalue = newvalue.view(-1)
                # Calculate the MSE loss between the returns and the value predictions of the critic
                # Clipping V loss is often not necessary and arguably worse in practice
                if self.args.clip_vloss:
                    v_loss_unclipped = (newvalue - b_returns[mb_inds]) ** 2
                    v_clipped = b_values[mb_inds] + torch.clamp(
                        newvalue - b_values[mb_inds],
                        -self.args.clip_coef,
                        self.args.clip_coef,
                    )
                    v_loss_clipped = (v_clipped - b_returns[mb_inds]) ** 2
                    v_loss_max = torch.max(v_loss_unclipped, v_loss_clipped)
                    v_loss = 0.5 * v_loss_max.mean()
                else:
                    v_loss = 0.5 * ((newvalue - b_returns[mb_inds]) ** 2).mean()

                # Add an entropy bonus to the loss
                entropy_loss = entropy.mean()
                loss = pg_loss - self.args.ent_coef * entropy_loss + v_loss * self.args.vf_coef

                # Backpropagation
                self.optimizer.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(self.agent.parameters(), self.args.max_grad_norm)
                self.optimizer.step()

            if self.args.target_kl is not None:
                if approx_kl > self.args.target_kl:
                    break

        y_pred, y_true = b_values.cpu().numpy(), b_returns.cpu().numpy()
        var_y = np.var(y_true)
        explained_var = np.nan if var_y == 0 else 1 - np.var(y_true - y_pred) / var_y

        # Infrequently save the model and evaluate the agent
        if (update - 1) % self.args.save_frequency == 0:
            start_eval = time.time()
            # Save the model
            run_path = files("cyberwheel.data.models").joinpath(self.args.experiment_name)
            if not os.path.exists(run_path):
                os.makedirs(run_path)
            agent_path = run_path.joinpath("agent.pt")
            globalstep_path = run_path.joinpath(f"{self.global_step}.pt")
            torch.save(self.agent.state_dict(), agent_path)
            torch.save(self.agent.state_dict(), globalstep_path)
            if self.args.track:
                import wandb
                wandb.save(
                    agent_path,
                    base_path=run_path,
                    policy="now",
                )
                wandb.save(
                    globalstep_path,
                    base_path=run_path,
                    policy="now",
                )

            # Run evaluation
            print("Evaluating Agent...")

            eval_results = self.run_evals(globalstep_path, self.global_step)

            # Log eval results
            (
                eval_network_config,
                eval_decoy_config,
                eval_reward_function,
                eval_red_agent,
                eval_return,
                eval_step,
            ) = eval_results
            self.writer.add_scalar(
                f"evaluation/{eval_network_config.split('.')[0]}_{eval_decoy_config}|{eval_reward_function}reward__{eval_red_agent}_episodic_return",
                eval_return,
                eval_step,
            )
            self.writer.add_scalar(
                "charts/eval_time", int(time.time() - start_eval), self.global_step
            )

        # TRY NOT TO MODIFY: record rewards for plotting purposes
        self.writer.add_scalar(
            "charts/learning_rate", self.optimizer.param_groups[0]["lr"], self.global_step
        )
        self.writer.add_scalar("losses/value_loss", v_loss.item(), self.global_step)
        self.writer.add_scalar("losses/policy_loss", pg_loss.item(), self.global_step)
        self.writer.add_scalar("losses/entropy", entropy_loss.item(), self.global_step)
        self.writer.add_scalar("losses/old_approx_kl", old_approx_kl.item(), self.global_step)
        self.writer.add_scalar("losses/approx_kl", approx_kl.item(), self.global_step)
        self.writer.add_scalar("losses/clipfrac", np.mean(clipfracs), self.global_step)
        self.writer.add_scalar("losses/explained_variance", explained_var, self.global_step)
        print("SPS:", int(self.global_step / (time.time() - self.start_time)))
        self.writer.add_scalar(
            "charts/SPS", int(self.global_step / (time.time() - self.start_time)), self.global_step
        )

    def close(self) -> None:
        self.envs.close()
        self.writer.close()