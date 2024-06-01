import os
from multiprocessing import Pool
import random

def run(command):
    os.system(command)

def main():
    random.seed()
    hosts = 2000
    args = []
    for i in range(10):
        args.append(f"python  ppo_cyberwheel.py --exp-name new-{hosts}-host-network-experiment-{i} --seed {random.randint(0,10000)} --device cuda:0 --num-envs 128  --total-timesteps 1920000  --network-config /home/70d/cyberwheel/cyberwheel/resources/metadata/{hosts}-host-network.yaml --async-env --min-decoys 2 --track --max-decoys 3 --num-hosts {hosts}")
    with Pool(10) as p:
        p.map(run, args)

if __name__ == "__main__":
    main()
