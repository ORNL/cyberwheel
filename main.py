from cyberwheel_envs.cyberwheel_singleagent import *
import os
from stable_baselines3.common.env_checker import check_env
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import SubprocVecEnv
from stable_baselines3.common.utils import set_random_seed
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import VecMonitor
from stable_baselines3.common.evaluation import evaluate_policy
from stable_baselines3.common.callbacks import EvalCallback

def make_env(env_id: str, rank: int, seed: int = 0):
    """
    Utility function for multiprocessed env.

    :param env_id: the environment ID
    :param num_env: the number of environments you wish to have in subprocesses
    :param seed: the inital seed for RNG
    :param rank: index of the subprocess
    """
    def _init():
        #env = SingleAgentCyberwheel(50,1,1)  # Create an instance of the Cyberwheel environment
        env = SingleAgentCyberwheel.create_from_yaml('network/example_config.yaml')
        env.reset(seed=seed + rank)  # Reset the environment with a specific seed
        log_file = f'monitor_vecenv_logs/{env_id}_{rank}'
        env = Monitor(env, log_file, allow_early_resets=True)
        return env

    set_random_seed(seed)  # Set the random seed for reproducibility
    return _init

def debug_env(env):
    # It will check your custom environment and output additional warnings if needed
    # Use this to debug changes but not when running - it can cause some meaningless errors on reset()
    env = SingleAgentCyberwheel.create_from_yaml('network/example_config.yaml')
    check_env(env)

def main():
    num_cpus = 1  # Number of CPUs to use for parallel environments
    #num_cpus = os.cpu_count()

    vec_env = SubprocVecEnv([make_env("cyberwheel", i) for i in range(num_cpus)])  # Create a vectorized environment with multiple instances of the Cyberwheel environment

    # Create the PPO model
    model = PPO("MlpPolicy", vec_env)

    #eval_callback = EvalCallback(env, best_model_save_path="best_model/",
     #                         log_path="monitor_eval_logs/", eval_freq=max(5000 // num_training_envs, 1),
      #                        n_eval_episodes=5, deterministic=True,
       #                       render=False)

    # Training the PPO model (you may need to adjust the number of steps and other hyperparameters)
    model.learn(total_timesteps=10000)
    #, callback=eval_callback)

    # Save the trained model
    #model.save("test")

    # Load the trained model
    #loaded_model = PPO.load("test")

    # Create a new environment to evaluate the trained model
    # evaluate_policy cannot use vectorized environments
    env = Monitor(SingleAgentCyberwheel.create_from_yaml('network/example_config.yaml'), 'monitor_logs/')

    mean_reward, std_reward = evaluate_policy(model, env, n_eval_episodes=10)
    print(f"Mean reward: {mean_reward} +/- {std_reward}")

if __name__ == '__main__':
    main()
