import argparse
import os

from distutils.util import strtobool

from cyberwheel.utils import YAMLConfig

def parse(config, mode: str = 'train'):
    args = YAMLConfig(config)
    args.parse_config()
    args_dict = vars(args)

    override_args = parse_eval_override_args() if mode == 'evaluate' else parse_override_args() if mode == 'train' else parse_default_override_args() if mode == 'run' else args
    override_args_dict = vars(override_args)
    for arg in override_args_dict:
        if arg in args_dict and override_args_dict[arg] != None and override_args_dict[arg] != "":
            setattr(args, arg, override_args_dict[arg])

    if args.deterministic:
        os.environ["CYBERWHEEL_DETERMINISTIC"] = 'true'
    else:
        os.environ["CYBERWHEEL_DETERMINISTIC"] = 'false'

    return args


def parse_override_args(print_help: bool = False):
    """
    Parses through any command line arguments for training. These will override any args set in the YAML config.
    """
    parser = argparse.ArgumentParser()
    training_group = parser.add_argument_group("Training Parameters", description="parameters to handle training options")
    env_group = parser.add_argument_group("Environment Parameters", description="parameters to handle Cyberwheel environment options")
    rl_group = parser.add_argument_group("Reinforcement Learning Parameters", description="parameters to handle various RL options")

    # Training Parameters
    training_group.add_argument("--experiment-name", type=str, help="The name of the experiment. This will be the name the model is saved locally and on W&B.")
    training_group.add_argument("--seed", type=int, help="seed of the experiment")
    training_group.add_argument("--deterministic", type=lambda x: bool(strtobool(x)), nargs="?", const=True, help="if toggled, `torch.backends.cudnn.deterministic=True`")
    training_group.add_argument("--device", type=str, help="Choose the device used for optimization. Choose 'cuda', 'cpu', or specify a gpu with 'cuda:0'")
    training_group.add_argument("--async-env", type=lambda x: bool(strtobool(x)), nargs="?", const=True, help="if toggled, uses AsyncVectorEnv instead of SyncVectorEnv")
    training_group.add_argument("--track", type=lambda x: bool(strtobool(x)), nargs="?", const=True, help="if toggled, this experiment will be tracked with Weights and Biases")
    training_group.add_argument("--wandb-project-name", type=str, help="the wandb's project name")
    training_group.add_argument("--wandb-entity", type=str, help="the entity (team) of wandb's project")
    training_group.add_argument("--total-timesteps", type=int, help="total timesteps of the experiments")
    training_group.add_argument("--num-saves", type=int, help="the number of model saves and evaluations to run throughout training")
    training_group.add_argument("--num-envs", type=int, help="the number of parallel game environments")
    training_group.add_argument("--num-steps", type=int, help="the number of steps to run in each environment per policy rollout")
    training_group.add_argument('--eval-episodes', type=int, help='Number of evaluation episodes to run')
    
    # Cyberwheel Environment Parameters
    env_group.add_argument("--environment", type=str, help="the environment class to use. Current options: CyberwheelRL | Cyberwheel")
    env_group.add_argument("--red-agent", type=str, help="the red agent config to train with. Current options: rl_red_agent.yaml | art_agent.yaml | inactive_red_agent.yaml")
    env_group.add_argument("--campaign", type=lambda x: bool(strtobool(x)), nargs="?", const=True, help="if toggled, uses ARTCampaign as red agent")
    env_group.add_argument("--train-red", type=lambda x: bool(strtobool(x)), nargs="?", const=True, help="toggle if you want to train the red agent")
    env_group.add_argument("--valid-targets", type=str, help="Hosts to consider as valid targets for red agent. Can be: 'HOST_NAME' | 'servers' | 'all'")
    env_group.add_argument("--blue-agent", type=str, help="the blue agent config to train with. Current options: rl_blue_agent.yaml | inactive_blue_agent.yaml")
    env_group.add_argument("--train-blue", type=lambda x: bool(strtobool(x)), nargs="?", const=True, help="toggle if you want to train the blue agent")
    env_group.add_argument("--network-config", help="Input the network config filename", type=str)
    env_group.add_argument("--decoy-config", help="Input the decoy config filename", type=str)
    env_group.add_argument("--host-config", help="Input the host config filename", type=str)
    env_group.add_argument("--reward-function", help="Which reward function to use. Current option: 'RLReward'", type=str)
    env_group.add_argument("--detector-config", help="Location of detector config file.", type=str)

    # RL Algorithm Parameters
    rl_group.add_argument("--env-id", type=str, help="the id of the environment")
    rl_group.add_argument("--learning-rate", type=float, help="the learning rate of the optimizer")
    rl_group.add_argument("--anneal-lr", type=lambda x: bool(strtobool(x)), nargs="?", const=True, help="Toggle learning rate annealing for policy and value networks")
    rl_group.add_argument("--gamma", type=float, help="the discount factor gamma")
    rl_group.add_argument("--gae-lambda", type=float, help="the lambda for the general advantage estimation")
    rl_group.add_argument("--num-minibatches", type=int, help="the number of mini-batches")
    rl_group.add_argument("--update-epochs", type=int, help="the K epochs to update the policy")
    rl_group.add_argument("--norm-adv", type=lambda x: bool(strtobool(x)), nargs="?", const=True, help="Toggles advantages normalization")
    rl_group.add_argument("--clip-coef", type=float, help="the surrogate clipping coefficient")
    rl_group.add_argument("--clip-vloss", type=lambda x: bool(strtobool(x)), nargs="?", const=True, help="Toggles whether or not to use a clipped loss for the value function, as per the paper.")
    rl_group.add_argument("--ent-coef", type=float, help="coefficient of the entropy")
    rl_group.add_argument("--vf-coef", type=float, help="coefficient of the value function")
    rl_group.add_argument("--max-grad-norm", type=float, help="the maximum norm for the gradient clipping")
    rl_group.add_argument("--target-kl", type=float, help="the target KL divergence threshold")

    if print_help:
        parser.parse_args()
        parser.print_help()
    else:
        return parser.parse_args()

def parse_eval_override_args(print_help: bool = False):
    """
    Parses through any command line arguments for evaluating. These will override any args set in the YAML config.
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("--red-agent", type=str, help="the red agent config to evaluate with. Current options: rl_red_agent.yaml | art_agent.yaml | inactive_red_agent.yaml")
    parser.add_argument("--blue-agent", type=str, help="the blue agent config to evaluate with. Current options: rl_blue_agent.yaml | inactive_blue_agent.yaml")
    parser.add_argument("--environment", type=str, help="the environment class to use. Current options: CyberwheelRL | Cyberwheel")
    parser.add_argument("--valid-targets", type=str, help="Hosts to consider as valid targets for red agent. Can be: 'HOST_NAME' | 'servers' | 'all'")
    parser.add_argument("--train-red", type=lambda x: bool(strtobool(x)), nargs="?", const=True, help="toggle if you want to train the red agent")
    parser.add_argument("--train-blue", type=lambda x: bool(strtobool(x)), nargs="?", const=True, help="toggle if you want to train the blue agent")
    parser.add_argument("--campaign", type=lambda x: bool(strtobool(x)), nargs="?", const=True, help="if toggled, uses ARTCampaign as red agent")
    parser.add_argument("--seed", type=int, help="seed of the experiment")
    parser.add_argument("--deterministic", type=lambda x: bool(strtobool(x)), nargs="?", const=True, help="if toggled, `torch.backends.cudnn.deterministic=True`")


    parser.add_argument("--download-model", type=lambda x: bool(strtobool(x)), nargs="?", const=True, help="Download agent model from WandB. If present, requires --run, --wandb-entity, --wandb-project-name flags.")
    parser.add_argument("--checkpoint", help="Which checkpoint of the model to evaluate. Defaults to 'agent' (latest).")
    parser.add_argument("--run", help="Run ID from WandB for pretrained blue agent to use. Required when downloading model from W&B")
    parser.add_argument("--experiment-name", help="Experiment name for storing/retrieving agent model")
    parser.add_argument("--visualize", type=lambda x: bool(strtobool(x)), nargs="?", const=True, help="Stores graphs of network state at each step/episode. Can be viewed in dash server.")
    parser.add_argument("--graph-name", help="Override naming convention of graph storage directory.")
    parser.add_argument("--network-config", help="Input the network config filename", type=str)
    parser.add_argument("--decoy-config", help="Input the decoy config filename", type=str)
    parser.add_argument("--host-config", help="Input the host config filename", type=str)
    parser.add_argument("--detector-config", help="Path to detector config file", type=str)
    parser.add_argument("--reward-function", help="Which reward function to use. Current option: 'RLReward' (default)", type=str)
    parser.add_argument("--num-steps", help="Number of steps per episode for evaluation", type=int)
    parser.add_argument("--num-episodes", help="Number of episodes to evaluate", type=int)
    parser.add_argument("--wandb-entity", help="Username where W&B model is stored. Required when downloading model from W&B", type=str)
    parser.add_argument("--wandb-project-name", help="Project name where W&B model is stored. Required when downloading model from W&B", type=str)

    if print_help:
        parser.parse_args()
        parser.print_help()
    else:
        return parser.parse_args()

def parse_default_override_args(print_help: bool = False):
    """
    Parses through any command line arguments for setting up environment. These will override any args set in the YAML config.
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("--environment", type=str, help="the environment class to use. Current options: CyberwheelRL | Cyberwheel")
    parser.add_argument("--experiment-name", help="Experiment name for storing/retrieving agent model")
    parser.add_argument("--network-config", help="Input the network config filename", type=str)
    parser.add_argument("--decoy-config", help="Input the decoy config filename", type=str)
    parser.add_argument("--host-config", help="Input the host config filename", type=str)
    parser.add_argument("--num-steps", help="Number of steps per episode for evaluation", type=int)
    parser.add_argument( "--num-episodes", help="Number of episodes to evaluate", type=int)
    parser.add_argument("--deterministic", type=lambda x: bool(strtobool(x)), nargs="?", const=True, help="if toggled, `torch.backends.cudnn.deterministic=True`")


    if print_help:
        parser.parse_args()
        parser.print_help()
    else:
        return parser.parse_args()