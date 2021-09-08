import unittest
import src.util as util


class TestUtil(unittest.TestCase):

    def test_util(self):
        u1, u2 = util.uniqueid(), util.uniqueid()
        assert u1 != u2

        l1 = util.log([])
        assert len(l1) == 1
        l2 = util.log(l1)
        assert len(l2) == len(l1) == 2

    def test_stack(self):
        st = util.get_stack()
        assert len(st) == 0
        exc = util.print_exc_plus()
        assert 'None' in exc
