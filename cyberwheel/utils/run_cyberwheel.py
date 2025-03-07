from cyberwheel.utils import YAMLConfig, parse_default_override_args, Runner

def run_cyberwheel(args: YAMLConfig):
    # Initialize the Evaluator object
    
    runner = Runner(args)

    # Configure training parameters and train
    runner.configure()

    runner.run()

    runner.close()
