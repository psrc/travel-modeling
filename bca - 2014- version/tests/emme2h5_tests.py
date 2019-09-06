from nose.tools import *
from bc2.emme2h5 import *
from array import array


class FakeEmmeMat:
    """
    A fake class to help aid testing of functions that work against
    Emme matrix objects
    """
    def get_data(self):
        return(FakeEmmeData())

class FakeEmmeData:
    """
    A fake class to help aid testing of functions that work against Emme
    matrix data objects
    """
    def __init__(self):
        # raw data has a gap in zone 3
        self.raw_data = [array('f', [1.1, 1.2, 1.4, 1.5, 0]),
                         array('f', [2.1, 2.2, 2.4, 2.5, 0]),
                         array('f', [4.1, 4.2, 4.4, 4.5, 0]),
                         array('f', [5.1, 5.2, 5.4, 5.5, 0]),
                         array('f', [0, 0, 0, 0, 0])]
    
        self.indices = [range(1, 6), range(1,6)]

    def get(self, p, q):
        if p > 3:
            x = p - 1
        else:
            x = p
        if q > 3:
            y = q - 1
        else:
            y = q
        if p == 3 or q == 3:
            x = 5
            y = 5
        else: pass

        return(self.raw_data[x-1][y-1])


def test_emmemat2np():
    emmefullmatrix = FakeEmmeMat()
    npmat = emmemat2np(emmefullmatrix)
    fakenp = np.matrix([array('f', [1.1, 1.2, 0, 1.4, 1.5]),
                        array('f', [2.1, 2.2, 0, 2.4, 2.5]),
                        array('f', [0, 0, 0, 0, 0]),
                        array('f', [4.1, 4.2, 0, 4.4, 4.5]),
                        array('f', [5.1, 5.2, 0, 5.4, 5.5])])
    np.testing.assert_array_equal(fakenp, npmat)
    
