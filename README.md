# Cyberwheel

A simulation environment for training autonomous cyber defense agents based on the Mitre Att&ck framework.

#### Contributing

- If you are not familiar with SOLID principles, please read this before contributing. Pretty basic, but makes a huge difference down the road --- [Article on SOLID](https://medium.com/@iclub-ideahub/the-solid-principles-a-guide-to-writing-maintainable-and-extensible-code-in-python-ecac4ea8d7ee).
- If you need to add dependency, this project is packaged with [poetry](https://python-poetry.org/). Please take a few minutes to [install](https://python-poetry.org/docs/#installation) and read about the [basics](https://python-poetry.org/docs/basic-usage/#specifying-dependencies) before adding any dependencies. Do not use pip, do not use requirements.txt. TLDR: use `poetry add <dependcy name>`. After adding your dependency, add and commit the new `poetry.lock` file.
- This project uses pre-commit to automatically run formatting prior to every commit. Pyright is included in this suite and _will_ block your commit if you commit code with bad type labels. If you'd like to skip this check for a WIP commit or some other reason, run `SKIP=pyright git commit <rest of commit command>`.
- If you need to do anything with the networkx graph, write helper functions in the network module (base class where possible) rather than passing the graph around / injecting it wherever possible. Of course you may have to inject the network instance since it holds the state information.
- The cyberwheel class that inherits from gym should contain minimal code to keep it clean. If you find yourself writing long code blocks in this file, consider whether they should be moved into another module or class. The same thing goes for the main class --- keep it clean. If you want to add 30 command line args, maybe find a way to parse them using a helper class just to keep that file clean.
- Be creative and have fun!
