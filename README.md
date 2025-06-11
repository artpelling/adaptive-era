[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.15586170.svg)](https://doi.org/10.5281/zenodo.15586170)
![Python Version from PEP 621 TOML](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2Fartpelling%2Fadaptive-era%2Frefs%2Fheads%2Fmain%2Fpyproject.toml)

# Code for Numerical Experiments in "Adaptive Reduced Order Modelling of Discrete-Time Systems with Input-Output Dead Time"

This repository contains code for numerical experiments reported in

> Art J. R. Pelling, Ennes Sarradj
> **Adaptive Reduced Order Modelling of Discrete-Time Systems with Input-Output Dead Time**,
> [*arXiv preprint*](https://doi.org/10.48550/arXiv.2506.08870),
> 2025

## Installation

To run the benchmarks from the paper, Python 3.12, `git` and a virtual environment is needed for which [`micromamba`](https://mamba.readthedocs.io/en/latest/user_guide/micromamba.html) (a drop in replacement for `conda`) is used here. In principle, the benchmarks could also be run with other tools like `virtualenv` or `uv`. We select `micromamba`, because it makes it easier to build NumPy from source.

All dependencies are listed in [`pyproject.toml`](pyproject.toml).

To install the `era_dts` package, create and activate a virtual environment:
``` shell
micromamba create -n era python=3.12
micromamba activate era
```

Clone the repository and install the package with:
``` shell
git clone https://github.com/artpelling/adaptive-era.git && cd adaptive-era
```

### Compiling NumPy with ILP64 support (optional)
In order to construct the larger models, we need to allocate arrays with more than 2<sup>31</sup>-1 elements. Therefore, we need to build NumPy against the ILP64 interface, using 64-bit instead of 32-bit integers for indexing. The install instructions in this subsection are somewhat specific to our machine, also consult the [NumPy docs](https://numpy.org/doc/stable/building/blas_lapack.html) for more.

Clone the [NumPy repo](https://github.com/numpy/numpy):
``` shell
git clone https://github.com/numpy/numpy.git && cd numpy
git submodule update --init
```

Checkout the latest release branch (2.2.4 in our case):
``` shell
git checkout v2.2.4
```

Install build dependencies:
``` shell
micromamba install gcc gxx clang mkl-devel -c conda-forge
```

Note that we install `mkl-devel` from the defaults channel in order to also install the `.pc` files. It might be necessary to point `pkg-config` to their location with:
``` shell
export PKG_CONFIG_PATH=~/.local/share/mamba/envs/era/lib/pkgconfig
```
The path to the virtual environment can of course differ. It can be easily found with `micromamba env list`.

Now compile NumPy with:
``` shell
pip install . -Csetup-args=-Dallow-noblas=false -Csetup-args=-Dcpu-baseline="native" -Csetup-args=-Dmkl-threading=gomp -Csetup-args=-Duse-ilp64=true
```

and exit the directory
``` shell
cd ..
```


### Install the package
Now, (whether we have successfully compiled NumPy with ILP64 interface or not), we can install the package with:
``` shell
pip install .
```


## Running the Experiments

The individual benchmarks from the paper can be run with the `run-benchmark` entry point, e.g.:
``` shell
run-benchmark -dte DTS MIRD -s SHORT3
```

Consult 
``` shell
run-benchmark -h
```
for options such as the dead time splitting algorithm and output directory and consult

``` shell
run-benchmark MIRD -h
run-benchmark MIRACLE -h
```
for a list of available scenarios.

The script will download the necessary data from the benchmark datasets and store them in the `raw` directory using the [`pooch` package](https://github.com/fatiando/pooch). The data validated against an `md5` hash to ensure reproducibility, post-processed and written to the `processed` directory. Subsequent calls to `run-benchmark` will use the processed data, if available.

### Recreating the figures

All benchmarks needed for the figures in the paper can be recreated handily with targets defined in the [`Makefile`](`Makefile`), e.g.:
``` shell
make all
```

After running the benchmarks, the results can be converted to a PGF-compatible `.txt` file (assuming the results are exported to the default `models` directory) with:
``` shell
txt4pgf
```


## Author

Art J. R. Pelling:

- affiliation: Technische Universität Berlin
- email: a.pelling@tu-berlin.de
- ORCiD: [0000-0003-3228-6069](https://orcid.org/0000-0003-3228-6069)

## License

The code is published under the [MIT LICENSE](LICENSE).
