#!/usr/bin/env python3

import numpy as np
from pathlib import Path

from era_dts.downloader import fetch_data
from era_dts.dead_time_extraction import split_delays
from era_dts.utils import estimate_delays


model_dir = Path('models')
pgfdata_dir = Path('pgfdata')
pgfdata_dir.mkdir(parents=True, exist_ok=True)


def export_txt(dataset, path):
    scenario, case = path.name.split('-')

    data = fetch_data(dataset, scenario)
    ir, fs = data['ir'], data['fs']
    ir = ir.astype(np.float32)
    T, p, m = ir.shape

    orders = np.load(path / 'orders.npy')
    dofs = (orders+m)*(orders+p)
    if case in ('LC', 'DTS'):
        d = estimate_delays(data['rpos'], data['spos'], 343, fs, subsample=False)
        if case == 'LC':
            dofs += min(m,p)*np.min(d)
        else:
            do, di = split_delays(d, subsample=True)
            dofs += (np.sum(do) + np.sum(di)).astype(int)
    irnorm = (np.load(path / 'err_true.npy')/np.load(path / 'err_relative.npy'))[0]
    err_rel = 20*np.log10(np.load(path / 'err_relative.npy'))
    kung = np.load(path / 'err_kung.npy')
    kung_new = 20*np.log10(kung)
    kung_old = 10*np.log10(kung/irnorm)
    loo = np.load(path / 'err_est.npy')
    loo = 20*np.log10(loo)

    np.savetxt(pgfdata_dir / f'{dataset}-{scenario}-{case}.txt',
               np.concatenate([orders, dofs, err_rel, loo, kung_new, kung_old]).reshape(6,-1).T,
               header='orders dofs err_rel loo kung_new kung_old',
               comments='')


def create_txt4pgf():
    for dataset in model_dir.glob('*'):
        for path in dataset.glob('*'):
            export_txt(dataset.name, path)
