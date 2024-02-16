# Cyberwheel

A simulation environment for training autonomous cyber defense agents based on the Mitre Att&ck framework.

#### Contributing

- If you are not familiar with SOLID principles, please read this before contributing. Pretty basic, but makse a huge difference down the road --- [Article on SOLID](https://medium.com/@iclub-ideahub/the-solid-principles-a-guide-to-writing-maintainable-and-extensible-code-in-python-ecac4ea8d7ee).
- If you need to add dependency, this project is packaged with [poetry](https://python-poetry.org/). Please take a few minutes to [install](https://python-poetry.org/docs/#installation) and read about the [basics](https://python-poetry.org/docs/basic-usage/#specifying-dependencies) before adding any dependencies. Do not use pip, do not use requirements.txt. TLDR: use `poetry add <dependcy name>`. After adding your dependency, add and commit the new `poetry.lock` file.
- If you need to do anything with the networkx graph, write helper functions in the network module (base class where possible) rather than passing the graph around / injecting it wherever possible. Of course you may have to inject the network instance since it holds the state information.
- The cyberwheel class that inherits from gym should contain minimal code to keep it clean. If you find yourself writing long code blocks in this file, consider whether they should be moved into another module or class. The same thing goes for the main class --- keep it clean. If you want to add 30 command line args, maybe find a way to parse them using a helper class just to keep that file clean.
- Be creative and have fun!

#### Running on CDAT

- To use the GPU, run with ```CUDA_VISIBLE_DEVICES="0" python main.py``` and set to desired CUDA device.
- You want environment running on cpus and policy training on gpus. Data is collected on cpus by the vector env then transferred to gpu for gradient calculations. So you can combine multiple CPUs and GPU effectively.

#### ToDos

- Network code - create base config files for different common topologies and modify network class so we can scale / randomize the exact layout if desired from the base topology definition
- Create class structure for detectors and red agent actions such that red agent could be RL-based. Map detectors back to observation space. Create heuristic based red agents.
- Design red agent observation space / red agent and blue agent interaction

#### Ideas

- Both red agent and blue agent practice deception - red agent can distract you or leverage automated response for DoS attack / segment network in useful way (when it looks like campaign X is happening, do this set of things - very reactive, assumes campaign happening). How to account for deception? Could AI pick up on that?
-
