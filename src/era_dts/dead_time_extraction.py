#!/usr/bin/env python3

import numpy as np
import scipy.sparse as sps
import scipy.optimize as spo

from era_dts.utils import estimate_dead_times, apply_dead_times


def split_dead_times(deltas, subsample=False):
    # construct A matrix for linear program
    p, m = deltas.shape
    A = sps.lil_array((m*p, m+p))
    if p > m:
        for i in range(p):
            A[i*m:(i+1)*m, i] = np.ones(m)
            A[i*m:(i+1)*m, p:] = np.eye(m)
        d = deltas.ravel(order='C')
        split = p
    else:
        for i in range(m):
            A[i*p:(i+1)*p, i] = np.ones(p)
            A[i*p:(i+1)*p, m:] = np.eye(p)
        A = sps.csr_array(A)
        d = deltas.T.ravel(order='C')
        split = m

    c = -np.ones(m+p)
    x = spo.linprog(c, A_ub=A, b_ub=d, method='highs-ipm')['x']

    if not subsample:
        x = x.astype(int)

    if p > m:
        do, di = np.split(x, [split])
        return do - np.min(do), di + np.min(do)
    else:
        di, do = np.split(x, [split])
        return do + np.min(di), di - np.min(di)


def extract_dead_times(ir, rpos, spos, fs, method):
    if method == 'NONE':
        return ir
    d = estimate_dead_times(rpos, spos, 343, fs, subsample=False)
    if method == 'LC':
        dest = np.ones_like(d)*np.min(d)
    elif method == 'DTS':
        do, di = split_dead_times(d, subsample=True)
        dest = np.add.outer(do, di)
    return apply_dead_times(ir, -dest.astype(int))
