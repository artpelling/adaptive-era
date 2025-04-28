#!/usr/bin/env python3

import numpy as np
import h5py as h5
import os
import pooch

from pathlib import Path
from scipy.io import loadmat
from zipfile import ZipFile


poochlog = pooch.get_logger()


miracle = pooch.create(
    base_url='https://depositonce.tu-berlin.de/bitstreams/',
    path='raw/MIRACLE',
    registry={
        'A1.h5': 'b0e053319fabad6964e2275f4bcd2dcfc6f0dc5f463e0324b7ad107e76612f88',
        'D1.h5': 'd888201065a43f436080da470f025c245b1a8030e08ea7a9dce1dc6b160761ee',
        'A2.h5': 'c021cc57bb51237283c5303e235495edfea75b1f0eaba4a8f988942b9913e7ff',
        'R2.h5': '479af6bfdd403c855d53304b291c4878c1f8d4a4482836de77677c03ffb6bbaa',
    },
    urls={
        'A1.h5': 'https://depositonce.tu-berlin.de/bitstreams/d5d90f86-a614-472c-b363-b3dd6139f5d6/download',
        'D1.h5': 'https://depositonce.tu-berlin.de/bitstreams/4b6cb9e5-f1e4-42c6-9b41-0a85e6ee9422/download',
        'A2.h5': 'https://depositonce.tu-berlin.de/bitstreams/3bd8541c-a9f5-4ea3-9d27-9699b8f859ca/download',
        'R2.h5': 'https://depositonce.tu-berlin.de/bitstreams/ccd132b6-9e1e-489a-b482-6d02ff3c0aac/download',
    }
)


mird = pooch.create(
    base_url='https://www.iks.rwth-aachen.de/fileadmin/user_upload/downloads/forschung/tools-downloads/',
    path='raw/MIRD',
    registry={
        'short_3.zip': None,
        'short_4.zip': None,
        'short_8.zip': None,
        'mid_3.zip': None,
        'mid_4.zip': None,
        'mid_8.zip': None,
        'long_3.zip': None,
        'long_4.zip': None,
        'long_8.zip': None,
    },
    urls={
        'short_3.zip': 'https://www.iks.rwth-aachen.de/fileadmin/user_upload/downloads/forschung/tools-downloads/Impulse_response_Acoustic_Lab_Bar-Ilan_University__Reverberation_0.160s__3-3-3-8-3-3-3.zip',
        'short_4.zip': 'https://www.iks.rwth-aachen.de/fileadmin/user_upload/downloads/forschung/tools-downloads/Impulse_response_Acoustic_Lab_Bar-Ilan_University__Reverberation_0.160s__4-4-4-8-4-4-4.zip',
        'short_8.zip': 'https://www.iks.rwth-aachen.de/fileadmin/user_upload/downloads/forschung/tools-downloads/Impulse_response_Acoustic_Lab_Bar-Ilan_University__Reverberation_0.160s__8-8-8-8-8-8-8.zip',
        'mid_3.zip': 'https://www.iks.rwth-aachen.de/fileadmin/user_upload/downloads/forschung/tools-downloads/Impulse_response_Acoustic_Lab_Bar-Ilan_University__Reverberation_0.360s__3-3-3-8-3-3-3.zip',
        'mid_4.zip': 'https://www.iks.rwth-aachen.de/fileadmin/user_upload/downloads/forschung/tools-downloads/Impulse_response_Acoustic_Lab_Bar-Ilan_University__Reverberation_0.360s__4-4-4-8-4-4-4.zip',
        'mid_8.zip': 'https://www.iks.rwth-aachen.de/fileadmin/user_upload/downloads/forschung/tools-downloads/Impulse_response_Acoustic_Lab_Bar-Ilan_University__Reverberation_0.360s__8-8-8-8-8-8-8.zip',
        'long_3.zip': 'https://www.iks.rwth-aachen.de/fileadmin/user_upload/downloads/forschung/tools-downloads/Impulse_response_Acoustic_Lab_Bar-Ilan_University__Reverberation_0.610s__3-3-3-8-3-3-3.zip',
        'long_4.zip': 'https://www.iks.rwth-aachen.de/fileadmin/user_upload/downloads/forschung/tools-downloads/Impulse_response_Acoustic_Lab_Bar-Ilan_University__Reverberation_0.610s__4-4-4-8-4-4-4.zip',
        'long_8.zip': 'https://www.iks.rwth-aachen.de/fileadmin/user_upload/downloads/forschung/tools-downloads/Impulse_response_Acoustic_Lab_Bar-Ilan_University__Reverberation_0.610s__8-8-8-8-8-8-8.zip',
    }
)


def process(func):
    def check_process(fname, action, pup):
        fname = Path(fname)
        outfile = (Path('processed') / fname.parent.name / fname.stem).with_suffix('.npz')
        if outfile.exists() and action == 'fetch':
            poochlog.info(f"Processed file '{outfile}' exists and is up to date.")
            return outfile
        else:
            poochlog.info(f"Processing file '{fname}' and writing to '{outfile}'.")
            outfile.parent.mkdir(parents=True, exist_ok=True)
            return func(fname, outfile)
    return check_process


@process
def process_miracle(infile, outfile):
    with h5.File(infile, 'r') as f:
        ir = f.get('data')['impulse_response'][()]
        fs = f.get('metadata')['sampling_rate'][()]
        spos = f.get('data')['location']['source'][()]
        rpos = f.get('data')['location']['receiver'][()]
    np.savez(outfile, ir=ir.T, fs=fs, spos=spos, rpos=rpos)
    return outfile


@process
def process_mird(infile, outfile):
    ir = np.empty((26, 8, 480000))
    spos = np.empty((26, 3))
    rpos = np.empty((8, 3))
    height = 1.2  # estimated from figure, as the paper does not say
    with ZipFile(infile, "r") as zip_file:
        for i, n in enumerate(zip_file.namelist()):
            d = n.split('_')[-4:]
            r, phi = float(d[2][0]), 2*np.pi*float(d[3][:3])/360
            spos[i] = r*np.sin(phi), r*np.cos(phi), height
            with open('tmp', 'wb') as tmpfile:
                tmpfile.write(zip_file.open(n).read())
            ir[i] = loadmat('tmp')['impulse_response'].T
    os.remove('tmp')
    spacing = float(d[1][0])/100 * np.arange(4) + 0.04
    rpos[:, 0] = np.concatenate([-spacing[::-1], spacing])
    rpos[:, 1] = np.zeros(8)
    rpos[:, 2] = height
    ir = ir.T
    # The IRs contain an additional dead time not explained by the source-receiver distance.
    # It is probably due to dead time in the measurement setup.
    # We compensate this by offsetting the IRs such that the offset plus the minimal geometric dead time equals 750.
    # The removal of 750 samples is done in several other papers using this dataset.
    offset = 629
    T60 = np.ceil(float(d[0][:-2])*48000).astype(int)
    noise = ir[-T60:]
    ir = ir[offset:T60+offset]
    np.savez(outfile, ir=ir, noise=noise, fs=48000, spos=spos, rpos=rpos)
    return outfile


def fetch_data(dataset, scenario):
    if dataset.upper() == 'MIRACLE':
        path = miracle.fetch(scenario[:2] + '.h5', progressbar=True, processor=process_miracle)
    elif dataset.upper() == 'MIRD':
        path = mird.fetch(scenario[:-1].lower() + '_' + scenario[-1] + '.zip', progressbar=True, processor=process_mird)

    data = dict(np.load(path))

    if dataset == 'MIRACLE' and scenario.endswith('_RED'):
        print('Subselecting a coarser grid (a quarter of the source locations).')
        idx = np.arange(4096).reshape(64, 64)[::2, ::2].reshape(1024)
        data['ir'] = data['ir'][..., idx]
        data['spos'] = data['spos'][idx]

    return data
