#!/usr/bin/env python3

import argparse
from pathlib import Path


parser = argparse.ArgumentParser()
parser.add_argument('-dte', '--dead-time-extraction', choices=['NONE', 'LC', 'DTS'], default='DTS', type=str.upper, help='The method for dead time extraction. Either the proposed dead time splitting method (DTS), extracting least-common dead time (LS), or no extraction (NONE). Defaults to DTS.', dest='dte')
parser.add_argument('-t', '--tolerances', type=float, nargs='+', default=(-1, -3, -6, -9, -12, -15, -18, -21, -24), help='Bound for the relative error of the constructed model in dB.', dest='tols')
parser.add_argument('-md', '--model-dir', type=Path, help='Directory where the models are stored.', default='models', dest='model_dir')
scenario_parsers = parser.add_subparsers(dest='dataset', description='The dataset to use.', help=f'Use "{__file__} {{MIRACLE,MIRD}} -h" to list available scenarios.')
miracle_parser = scenario_parsers.add_parser('MIRACLE', help='Microphone Array Impulse Repsonse Database for Acoustic Learning.')
mird_parser = scenario_parsers.add_parser('MIRD', help='Multi-Channel Impulse Response Database.')

miracle_parser.add_argument('-s', '--scenario', choices=['D1', 'A1', 'A1_RED', 'A2', 'A2_RED', 'R2', 'R2_RED'], type=str.upper, help='The scenario to consider.')
mird_parser.add_argument('-s', '--scenario', choices=['SHORT3', 'MID3', 'LONG3', 'SHORT4', 'MID4', 'LONG4', 'SHORT8', 'MID8', 'LONG8'], type=str.upper, help='The scenario to consider. SHORT MID LONG refers to the different T60s, the last digit refers to the inter-microphone spacings of the microphone array.')

args = parser.parse_args()


def run():
    from era_dts.construct import construct
    from pymor.tools.random import new_rng
    with new_rng(0):
        construct(**vars(args))
