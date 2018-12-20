import unittest

# import your test modules
from tests import test_crontab, test_utils

# initialize the test suite
loader = unittest.TestLoader()
suite = unittest.TestSuite()

# add tests to the test suite
suite.addTests(loader.loadTestsFromModule(test_crontab))
suite.addTests(loader.loadTestsFromModule(test_utils))

# initialize a runner, pass it your suite and run it
runner = unittest.TextTestRunner()
runner.run(suite)
