# This code is part of Qiskit.
#
# (C) Copyright IBM 2020, 2021.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

""" Test Portfolio """

import unittest
from test import QiskitFinanceTestCase

import datetime
import numpy as np

from qiskit_optimization.applications.ising.common import sample_most_likely
from qiskit import BasicAer
from qiskit.utils import aqua_globals, QuantumInstance
from qiskit.algorithms import NumPyMinimumEigensolver, QAOA
from qiskit.algorithms.optimizers import COBYLA
from qiskit_finance.applications.ising import portfolio
from qiskit_finance.data_providers import RandomDataProvider


class TestPortfolio(QiskitFinanceTestCase):
    """Tests Portfolio Ising translator."""

    def setUp(self):
        super().setUp()
        self.seed = 50
        aqua_globals.random_seed = self.seed

        num_assets = 4
        stocks = [("TICKER%s" % i) for i in range(num_assets)]
        data = RandomDataProvider(tickers=stocks,
                                  start=datetime.datetime(2016, 1, 1),
                                  end=datetime.datetime(2016, 1, 30),
                                  seed=self.seed)
        data.run()
        self.muu = data.get_period_return_mean_vector()
        self.sigma = data.get_period_return_covariance_matrix()

        self.risk = 0.5
        self.budget = int(num_assets / 2)
        self.penalty = num_assets
        self.qubit_op, self.offset = portfolio.get_operator(
            self.muu, self.sigma, self.risk, self.budget, self.penalty)

    def test_portfolio(self):
        """ portfolio test """
        algo = NumPyMinimumEigensolver()
        result = algo.compute_minimum_eigenvalue(operator=self.qubit_op)
        selection = sample_most_likely(result.eigenstate)
        value = portfolio.portfolio_value(
            selection, self.muu, self.sigma, self.risk, self.budget, self.penalty)
        np.testing.assert_array_equal(selection, [0, 1, 1, 0])
        self.assertAlmostEqual(value, -0.00679917)

    def test_portfolio_qaoa(self):
        """ portfolio test with QAOA """
        backend = BasicAer.get_backend('statevector_simulator')
        quantum_instance = QuantumInstance(backend=backend,
                                           seed_simulator=self.seed,
                                           seed_transpiler=self.seed)
        qaoa = QAOA(optimizer=COBYLA(maxiter=500),
                    initial_point=[0., 0.],
                    quantum_instance=quantum_instance)
        result = qaoa.compute_minimum_eigenvalue(operator=self.qubit_op)
        selection = sample_most_likely(result.eigenstate)
        value = portfolio.portfolio_value(
            selection, self.muu, self.sigma, self.risk, self.budget, self.penalty)
        np.testing.assert_array_equal(selection, [0, 1, 1, 0])
        self.assertAlmostEqual(value, -0.00679917)


if __name__ == '__main__':
    unittest.main()
