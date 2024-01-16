from pettingzoo.test import parallel_api_test
from cyberwheel_multiagent import MultiagentCyberwheel

if __name__ == "__main__":
    env = MultiagentCyberwheel()

    # Test to verify the environment is compliant with the API
    parallel_api_test(env, num_cycles=1_000_000)