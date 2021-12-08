import sys
import unittest
import ergo.util as util


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

        def f1():
            def f2():
                def f3():
                    try:
                        raise IndexError('zeke')
                    except IndexError as e:
                        return util.get_stack()
                return f3()
            return f2()

        frames = f1()
        for code, frame in zip(['f3', 'f2', 'f1'], frames):
            assert code in str(frame.f_code), f'code is: {code}, frame is: {frame}'

    def test_extract(self):
        def f3():
            raise IndexError('zeke')

        def f2():
            try:
                f3()
            except IndexError as inner_e:
                raise ValueError('reyna') from inner_e

        def f1():
            try:
                f2()
            except Exception as e:
                return util.extract_from_stack(e)

        filename, lineno, function_name = f1()
        assert filename == 'test_util.py'
        assert lineno == '45'
        assert function_name == 'f2'