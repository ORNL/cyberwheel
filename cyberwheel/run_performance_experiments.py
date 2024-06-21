import os
from multiprocessing import Pool
import random

def run(command):
    os.system(command)

def main():
    random.seed()
    hosts = 10
    args = []
    for i in range(10, 20, 10):
        for j in range(i, 11*i, i):
            timesteps = j * 128 * 300
            args.append(f"python  ppo_cyberwheel.py --exp-name new-{i}-hosts-step-experiment-{j} --seed {random.randint(0,10000)} \
                            --device cuda:0 --num-envs 128  --total-timesteps {timesteps}  --network-config /home/70d/cyberwheel/cyberwheel/network/{i}-host-network.yaml \
                            --async-env --min-decoys 3 --max-decoys 5 --num-hosts {i} --num-steps {j} --detector-config nids.yaml --track")
    with Pool(5) as p:
        p.map(run, args)

if __name__ == "__main__":
    main()
