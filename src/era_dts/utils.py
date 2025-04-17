#!/usr/bin/env python3

import numpy as np
import scipy.sparse as sps

from scipy.spatial.distance import cdist
from tqdm import tqdm


def estimate_delays(spos, rpos, c0, fs, subsample=False):
    d = cdist(spos, rpos)/c0*fs
    if not subsample:
        d = d.astype(int)
    return d


def apply_delays(ir, delays):
    irm = np.zeros_like(ir)
    p, m = ir.shape[1:]
    for i in range(p):
        for j in range(m):
            if delays[i, j] == 0:
                irm[:, i, j] = ir[:, i, j]
            if delays[i, j] > 1:
                irm[delays[i, j]:, i, j] = ir[:-delays[i, j], i, j]
            else:
                irm[:delays[i, j], i, j] = ir[-delays[i, j]:, i, j]
    return irm


def impulse_response(sys):
    A, B, C, D, _ = sys.to_matrices()
    y = np.zeros((sys.T, sys.dim_output, sys.dim_input))
    if D is not None:
        y[0] = D.todense() if sps.issparse(D) else D
    x = B
    for i in tqdm(range(1, sys.T), initial=1, total=sys.T, desc=f'n={sys.order}, m={sys.dim_input}, p={sys.dim_output}'):
        z = np.real(C @ x)
        y[i] = z.todense() if sps.issparse(z) else z
        x = A @ x
    return y
