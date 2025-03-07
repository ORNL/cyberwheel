from cyberwheel.utils import parse, YAMLConfig, Evaluator


def evaluate_cyberwheel(args: YAMLConfig):
    """
    This script will evaluate cyberwheel. Using the args from the config file passed, it will evaluate a pre-trained model and evaluate.
    Can fetch models from W&B, as well as use any stored in cyberwheel/data/models
    """
    args.evaluation = True

    # Initialize the Evaluator object
    evaluator = Evaluator(args)

    # Configure training parameters and train
    evaluator.configure_evaluation()

    evaluator.evaluate()
