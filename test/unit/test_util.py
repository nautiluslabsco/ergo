import unittest
from src.util import uniqueid


class TestUtil(unittest.TestCase):

    def test_util(self):
        u1, u2 = uniqueid(), uniqueid()
        assert u1 != u2
