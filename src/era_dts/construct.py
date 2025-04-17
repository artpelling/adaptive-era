 #!/usr/bin/env python3

import numpy as np
from scipy.fft import set_workers
import scipy.linalg as spla
from pathlib import Path
from time import perf_counter

from pymor.core.logger import set_log_levels
from pymor.tools.random import new_rng

from era_dts.downloader import fetch_data
from era_dts.dead_time_extraction import extract_dead_times
from era_dts.utils import impulse_response
from era_dts.era import RandomizedERAReductor


set_log_levels({
    'pymor.algorithms.chol_qr': 'WARNING',
})

# COMPUTATIONAL PARAMETERS
dtype = np.float32
qr_opts = {'orth_tol': 1e-6, 'maxiter': 10}
rrf_opts = {'block_size': 5, 'power_iterations': 2, 'qr_method': 'shifted_chol_qr', 'error_estimator': 'loo', 'qr_opts': qr_opts}
era_opts = {'force_stability': False, 'rrf_opts': rrf_opts}


def construct(dataset, scenario, dte, tols, model_dir, dist=None):
    model_dir = Path(model_dir) / dataset.upper() / (scenario + f'-{dte}')
    model_dir.mkdir(parents=True, exist_ok=True)

    tols = 10**(np.array(tols)/20)

    # Load Data
    data = fetch_data(dataset, scenario)
    ir, fs, rpos, spos = data['ir'], data['fs'], data['rpos'], data['spos']
    ir = ir.astype(dtype)

    tic = perf_counter()

    # Dead Time Extraction
    irm = extract_dead_times(ir, rpos, spos, fs, dte)

    # Run main identification loop
    orders, err_true, err_est, err_kung = [], [], [], []
    irnorm = spla.norm(irm)
    era = RandomizedERAReductor(irm[1:], 1/fs, feedthrough=irm[0], **era_opts)
    with (set_workers(20), new_rng(0)):
        for tol in tols:
            rom = era.reduce(tol=tol)
            orders.append(rom.order)
            hm = impulse_response(rom.with_(T=ir.shape[0]))
            err_true.append(spla.norm(irm-hm))
            err_est.append(era._rrf.estimate_error()/era._weighted_h2_norm())
            err_kung.append(era.error_bounds()[-1])

            print(f'order:\t\t\t{orders[-1]}')
            print(f'elapsed time:\t{perf_counter()-tic:.1f} s')
            print(f'est. error:\t{err_est[-1]:.5f}')
            print(f'rel. error:\t{err_true[-1]/irnorm:.5f}')
            print('\n')

            # save results
            model_file = (model_dir / f'rom_{orders[-1]}').with_suffix('.mat')
            rom.to_mat_file(model_file)
            np.save(model_dir / f'hsv_{orders[-1]}', rom.hsv())
            np.save(model_dir / 'orders', np.array(orders))
            np.save(model_dir / 'err_true', np.array(err_true))
            np.save(model_dir / 'err_relative', np.array(err_true)/irnorm)
            np.save(model_dir / 'err_est', np.array(err_est))
            np.save(model_dir / 'err_kung', np.array(err_kung)/irnorm)

            # adapt block size
            if rom.order < 50:
                era._rrf.block_size = 5
            elif rom.order < 100:
                era._rrf.block_size = 10
            elif rom.order < 400:
                era._rrf.block_size = 50
            elif rom.order < 1000:
                era._rrf.block_size = 100
            else:
                era._rrf.block_size = 250
