#!/usr/bin/env python3

import numpy as np

from era_dts.fastoperators import NumbaHankelOperator

from pymor.reductors.era import RandomizedERAReductor as pyMORRandomizedERAReductor
from pymor.algorithms.rand_la import RandomizedSVD


class RandomizedERAReductor(pyMORRandomizedERAReductor):
    def __init__(self, data, sampling_time, force_stability=True, feedthrough=None, allow_transpose=True,
                 power_iterations=2, rrf_args=None, num_left=None, num_right=None):
        # Initialize pyMOR's ERA base without constructing its standard Hankel operator.
        super(pyMORRandomizedERAReductor, self).__init__(
            data, sampling_time, force_stability=force_stability, feedthrough=feedthrough)
        self.__auto_init(locals())
        if rrf_args is not None and 'error_estimator' in rrf_args:
            assert rrf_args['error_estimator'] == 'loo', 'Only the leave-one-out error estimator is supported.'
        if num_left is not None or num_right is not None:
            self.logger.info('Computing the projected Markov parameters ...')
            data = self._project_markov_parameters(num_left, num_right)
        s = data.shape[0] if self.force_stability else (data.shape[0] + 1) // 2
        self._transpose = (data.shape[1] < data.shape[2]) if allow_transpose else False
        self._H = NumbaHankelOperator(data) if self.force_stability else NumbaHankelOperator(data[:s], r=data[s-1:])
        if self._transpose:
            self.logger.info('Using transposed formulation.')
            self._H = self._H.H
        rrf_args = {'qr_method': 'shifted_chol_qr', **(rrf_args or {}), 'error_estimator': 'loo'}
        self.randomized_svd = RandomizedSVD(
            self._H, power_iterations=power_iterations, low_rank_svd_method='scipy_svd', rrf_args=rrf_args)
        range_finder = self.randomized_svd.range_finder
        range_finder.Omega = self._H.range.make_array(np.empty((self._H.range.dim, 0), dtype=data.dtype))
        range_finder.Q = [self._H.range.make_array(np.empty((self._H.range.dim, 0), dtype=data.dtype))
                          for _ in range(power_iterations + 1)]
        range_finder.R = [np.empty((0, 0), dtype=data.dtype) for _ in range(power_iterations + 1)]
        self.randomized_svd.B = self._H.source.make_array(np.empty((self._H.source.dim, 0), dtype=data.dtype))
        range_finder._draw_samples = self._draw_samples

    def _draw_samples(self, num):
        # Faster random samples for Hankel matrices; pyMOR VectorArrays are dim-by-count.
        self.randomized_svd.range_finder.logger.info(f'Taking {num} samples ...')
        V = np.zeros((self._H._circulant.source.dim, num), dtype=self.data.dtype)
        V[:self._H.source.dim] = self._H.source.random(num, distribution='normal').to_numpy()
        return self._H.range.make_array(self._H._circulant._circular_matvec(V)[:self._H.range.dim])
