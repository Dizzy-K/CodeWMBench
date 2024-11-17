# Code from the article "CodeWMBench: An Automated Benchmark for Code Watermarking Evaluation"

ACM-TURC '24: Proceedings of the ACM Turing Award Celebration Conference - China 2024 [Accepted](https://dl.acm.org/doi/10.1145/3674399.3674447)

All the regeneration codes can be found in the [attack_box](https://github.com/Dizzy-K/CodeWMBench/tree/main/attack_box) folder, and the original data generation codes can be found in the [datagen](https://github.com/Dizzy-K/CodeWMBench/tree/main/datagen) folder

## Experimental Reproduction

First, refer to the execution of [datagen](https://github.com/Dizzy-K/CodeWMBench/tree/main/datagen) to obtain the initial data set, and then obtain the watermark data set according to the watermark embedding project. Finally, execute the files in [attack_box](https://github.com/Dizzy-K/CodeWMBench/tree/main/attack_box) again to regenerate the perturbation to detect the robustness of the watermark algorithm.

Specifically, execute the following code

```bash
python3 datagen/code_datagen.py
python3 rewrite.py
python3 retrans.py
```

## Citation format

```bib
@inproceedings{10.1145/3674399.3674447,
author = {Wu, BenLong and Chen, Kejiang and He, Yanru and Chen, Guoqiang and Zhang, Weiming and Yu, Nenghai},
title = {CodeWMBench: An Automated Benchmark for Code Watermarking Evaluation},
year = {2024},
isbn = {9798400710117},
publisher = {Association for Computing Machinery},
address = {New York, NY, USA},
url = {https://doi.org/10.1145/3674399.3674447},
doi = {10.1145/3674399.3674447},
pages = {120–125},
numpages = {6},
keywords = {Programming language model, benchmark, code watermark},
location = {Changsha, China},
series = {ACM-TURC '24}
}
```
