from nose.tools import *
from bc2.bc2 import *
import numpy as np

# Basic configuration dict, with fake values of time
config = {'Description': 'Test',
          'vot': {
              'class1': {'time1': 3., 'time2': 7.},
              'class2': {'time1': 0., 'time2': 1.}}}

# Fake benefit component with precomputed benefits
fakezzcomp1 = {'costunits':'minutes',
               'description': 'C1T1',
               'timeperiod': 'time1',
               'userclass': 'class1',
               'basecost': np.array([[1.,3.], [5.,np.nan]]),
               'altcost': np.array([[2.,4.], [6., 8.]]),
               'basevol': np.array([[0.,1.], [2.,3.]]),
               'altvol': np.array([[0.,2.], [4.,6.]]),
               'rawben': np.array([[0.,-1.5], [-3., np.nan]]),
               'dollarben': np.array([[0.,-0.075],[-0.15,np.nan]])}


def test_calc_zz_benefit():
    np.testing.assert_allclose(
        calc_zz_benefit(fakezzcomp1),
        fakezzcomp1['rawben'])

def test_min_to_dollars():
    np.testing.assert_allclose(
        to_dollars(fakezzcomp1, config),
        fakezzcomp1['dollarben'])

def test_dollars_to_dollars():
    fakedollars = fakezzcomp1
    fakedollars['costunits'] = 'dollars'
    fakedollars['dollarben'] = fakedollars['rawben']

    np.testing.assert_allclose(
        to_dollars(fakedollars, config),
        fakedollars['dollarben'])

def test_cents_to_dollars():
    fakecents = fakezzcomp1
    fakecents['costunits'] = 'cents'
    fakecents['dollarben'] = np.array([[0.,-0.15],[-0.3,np.nan]])

    np.testing.assert_allclose(
        to_dollars(fakecents, config),
        fakecents['dollarben'])
