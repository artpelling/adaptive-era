#!/usr/bin/env python3

import numpy as np

from era_dts.fastoperators import NumbaHankelOperator

from pymor.reductors.era import RandomizedERAReductor as pyMORRandomizedERAReductor
from pymor.algorithms.rand_la import RandomizedRangeFinder


class RandomizedERAReductor(pyMORRandomizedERAReductor):
    def __init__(self, data, sampling_time, force_stability=True, feedthrough=None, allow_transpose=True, rrf_opts={},
                 num_left=None, num_right=None):
        super(pyMORRandomizedERAReductor, self).__init__(data, sampling_time, force_stability=force_stability, feedthrough=feedthrough)
        self.__auto_init(locals())
        #data = data.copy()
        if num_left is not None or num_right is not None:
            self.logger.info('Computing the projected Markov parameters ...')
            data = self._project_markov_parameters(num_left, num_right)
        if self.force_stability:
            data = np.concatenate([data, np.zeros_like(data)[1:]], axis=0)
        s = (data.shape[0] + 1) // 2
        self._transpose = (data.shape[1] < data.shape[2]) if allow_transpose else False
        self._H = NumbaHankelOperator(data[:s], r=data[s-1:])
        if self._transpose:
            self.logger.info('Using transposed formulation.')
            self._H = self._H.H

        # monkey patch RRF with dtype of data for memory efficiency
        dtype = data.dtype
        self._last_sv_U_V = None
        self._rrf = RandomizedRangeFinder(self._H, **rrf_opts)
        self._rrf.Omega = self._rrf.A.range.make_array(np.empty((0, self._rrf.A.range.dim), dtype=dtype))
        self._rrf.estimator_last_basis_size, self.last_estimated_error = 0, np.inf
        self._rrf.Q = [self._rrf.A.range.make_array(np.empty((0, self._rrf.A.range.dim), dtype=dtype)) for _ in range(self._rrf.power_iterations+1)]
        self._rrf.R = [np.empty((0,0), dtype=dtype) for _ in range(self._rrf.power_iterations+1)]
        self._rrf._draw_samples = self._draw_samples

    def _draw_samples(self, num):
        # faster way of computing the random samples for Hankel matrices
        self._rrf.logger.info(f'Taking {num} samples ...')
        dtype = self.data.dtype
        V = np.zeros((self._H._circulant.source.dim, num), dtype=dtype)
        V[:self._H.source.dim] = self._H.source.random(num, distribution='normal').to_numpy().T
        return self._H.range.make_array(self._H._circulant._circular_matvec(V)[:, :self._H.range.dim])
