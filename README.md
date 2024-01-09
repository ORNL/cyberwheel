# Cyberwheel

#### Running on CDAT 

- To use the GPU, run with ```CUDA_VISIBLE_DEVICES="0" python main.py``` and set to desired CUDA device. 
- You want environment running on cpus and policy training on gpus. Data is collected on cpus by the vector env then transferred to gpu for gradient calculations. So you can combine multiple CPUs and GPU effectively. 