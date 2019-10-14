import os
import pprint
import unittest
from unittest.mock import MagicMock

from circleci.api import Api
from circleci.error import BadKeyError, BadVerbError, InvalidFilterError


class TestCircleCIApi(unittest.TestCase):

    def setUp(self):
        self.c = Api(os.getenv('CIRCLE_TOKEN'))

    def loadMock(self, filename):
        """helper function to open mock responses"""
        filename = 'tests/mocks/{0}'.format(filename)

        with open(filename, 'r') as f:
            self.c._request = MagicMock(return_value=f.read())

    def test_bad_verb(self):

        with self.assertRaises(BadVerbError) as e:
            self.c._request('BAD', 'dummy')

        self.assertEqual('BAD', e.exception.argument)
        self.assertIn('DELETE', e.exception.message)
