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

    def test_load_source(self):
        # load callable
        product = util.load_source("test/integration/target.py:product")
        assert product is not None
        assert product(4, 5) == 20

        # load classname
        product_cls = util.load_source("test/integration/target.py:Product")
        assert isinstance(product_cls(), object)
        assert product_cls()(4, 5) == 20

        # load classmethod
        product_call = util.load_source("test/integration/target.py:Product.__call__")
        assert product_call(product_cls(), 4, 5) == 20

        # load invalid pattern
        self.assertRaises(Exception, util.load_source, "test/integration/.target:py.__Product__+call")
