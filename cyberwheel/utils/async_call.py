from importlib.resources import files
import gymnasium as gym
from cyberwheel.network.network_base import Network

def make_env(env_func, args, networks, rank, evaluation: bool = False) -> function:
    """
    Utility function for multiprocessed env.

    :param env_id: the environment ID
    :param num_env: the number of environments you wish to have in subprocesses
    :param rank: index of the subprocess
    """

    def _init():
        if evaluation:
            config_path = files("cyberwheel.data.configs.network").joinpath(args.network_config)
            env = env_func(args, network=Network.create_network_from_yaml(config_path), evaluation=True)
        else:
            env = env_func(args, network=networks[rank], evaluation=False)
        _init.max_action_space_size = env.max_action_space_size
        env.reset()
        result = gym.wrappers.RecordEpisodeStatistics(env)  # This tracks the rewards of the environment that it wraps. Used for logging
        return result 
    return _init

def async_call(env_funcs):
    return gym.vector.AsyncVectorEnv(env_funcs)