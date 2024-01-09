from cyberwheel import *
from stable_baselines3.common.env_checker import check_env
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import SubprocVecEnv
from stable_baselines3.common.utils import set_random_seed
from stable_baselines3.common.monitor import Monitor


def make_env(env_id: str, rank: int, seed: int = 0):
    """
    Utility function for multiprocessed env.

    :param env_id: the environment ID
    :param num_env: the number of environments you wish to have in subprocesses
    :param seed: the inital seed for RNG
    :param rank: index of the subprocess
    """
    def _init():
        env = Cyberwheel(50,1,1)
        env.reset(seed=seed + rank)
        env = Monitor(env, 'monitor_logs/')
        return env

    set_random_seed(seed)
    return _init

def main():

    num_cpus = 1

    vec_env = SubprocVecEnv([make_env("cyberwheel", i) for i in range(num_cpus)])

    #env = Cyberwheel(50,5,1)


    # It will check your custom environment and output additional warnings if needed
    # Use this to debug changes but not when running - it can cause some meaningless errors on reset()
    # check_env(env)

    # Create the PPO model
    model = PPO("MlpPolicy", vec_env, verbose=1, n_steps=100)

    # Training the PPO model (you may need to adjust the number of steps and other hyperparameters)
    model.learn(total_timesteps=10000)

    # Save the trained model
    #model.save("test")

    # Load the trained model
    #loaded_model = PPO.load("test")

    obs = vec_env.reset()
    for _ in range(1000):
        action, _states = model.predict(obs)
        obs, rewards, dones, info = vec_env.step(action)
        #vec_env.render()

        # Check if all environments are done
        if np.all(dones):
            # Print rewards for each environment in the vector
            for i, reward in enumerate(rewards):
                print(f"Environment {i}: Reward: {reward}")

if __name__ == '__main__':
    main()