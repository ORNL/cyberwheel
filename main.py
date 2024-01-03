from cyberwheel import *
from stable_baselines3.common.env_checker import check_env
from stable_baselines3 import PPO

env = Cyberwheel(3,3,1)

# It will check your custom environment and output additional warnings if needed
check_env(env)

# Create the PPO model
model = PPO("MlpPolicy", env, verbose=1)

# Training the PPO model (you may need to adjust the number of steps and other hyperparameters)
model.learn(total_timesteps=10000)

# Save the trained model
model.save("ppo_network_model")

# Load the trained model
loaded_model = PPO.load("ppo_network_model")

# Example of using the trained model to perform actions in the environment
obs = env.reset()
for _ in range(1000):
    action, _ = loaded_model.predict(obs)
    obs, reward, done, _ = env.step(action)
    # env.render() not implemented

env.close()