# CleanRL script for training Cage Challenge 2 agents. CleanRL documentation can be found at https://docs.cleanrl.dev/,
import os
import time

from cyberwheel.utils import parse_override_args, YAMLConfig, Trainer

"""
This script will train cyberwheel. Using the args from the config file passed, it will run an Actor-Critic RL algorithm and run training
with intermittent evaluations/saves. If tracking to W&B, this will be logged in your W&B project for each training run.
"""
# Allows using command line to override args in the YAML config
def train_cyberwheel(args: YAMLConfig):
    args.batch_size = int(args.num_envs * args.num_steps)   # Number of environment steps to performa backprop with
    args.minibatch_size = int(args.batch_size // args.num_minibatches)  # Number of environments steps to perform backprop with in each epoch
    args.num_updates = args.total_timesteps // args.batch_size  # Total number of policy update phases
    args.save_frequency = int(args.num_updates / args.num_saves)    # Number of policy updates between each model save and evaluation
    if args.save_frequency == 0:
        args.save_frequency = 1
    args.num_updates = args.total_timesteps // args.batch_size

    # Unique experiment name if empty
    if not args.experiment_name:
        args.experiment_name = f"{os.path.basename(__file__).rstrip('.py')}_{args.seed}_{int(time.time())}"

    args.evaluation = False

    # Initialize the Trainer object
    trainer = Trainer(args)

    # Setup W&B if tracking
    if args.track:
        trainer.wandb_setup()

    # Configure training parameters and train
    trainer.configure_training()

    for update in range(1, args.num_updates + 1):
        trainer.train(update)

    trainer.close()
