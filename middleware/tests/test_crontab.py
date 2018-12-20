import os
from unittest import TestCase

import crontab


class TestCrontab(TestCase):
    def test_get_crons(self):
        """Only elements of config with keys starting with CRON_ should be
        returned."""
        config = {
            'A_0': 1,
            'B_2': 2,
            'CRON_12093': 6,
            'MACRON_k': 7,
            'CRON_1': 9,
            'CRON_651': 10
        }
        crons = crontab.get_crons(config)

        assert(crons == [6, 9, 10])

    def test_write_crons(self):
        """The content gets written correctly and in the right order"""
        crons = ['a', 'c']
        file = './temporary_test_file'
        crontab.write_crons(crons, file)
        expectedResponse = 'a\nc\n'
        with open('./temporary_test_file', 'r') as file:
            response = file.read()
        os.remove('./temporary_test_file')
            
        assert(response == expectedResponse)
