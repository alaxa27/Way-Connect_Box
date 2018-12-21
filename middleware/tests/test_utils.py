import traceback
from unittest import TestCase
from unittest.mock import patch

import utils


class TestUtils(TestCase):
    def test_str_deep_replace(self):
        """Dumb string.replace; it should always respect the occurence"""
        occ = 'LKJfezFE'
        result = utils.str_deep_replace('OIEFHAOFHoIJfeozij', occ, 'test')
        assert('test' not in result)
        result = utils.str_deep_replace(
            'OIEFHALKJfezFEOFHoIJfeozij',
            occ,
            'test'
            )
        assert('test' in result)

    def test_list_deep_replace(self):
        """It should replace the strings with the given occurrence in an
        array"""
        occ = 'MLKMLK'
        deep_list = ['aziufoiea', 'lkfajekfjMLKMLKdzahfi']
        result = utils.list_deep_replace(deep_list, occ, 'test')

        assert('test' not in result[0])
        assert('test' in result[1])

    def test_dict_deep_replace(self):
        """It should replaces the strings with occurrence in a dict"""
        occ = 'ABCDEF'
        deep_dict = {
            'A': 'Llfe',
            'B': 'OIFeofizejABCDEFmkfez'
        } 
        result = utils.dict_deep_replace(deep_dict, occ, 'test')

        assert('test' not in result['A'])
        assert('test' in result['B'])

    @patch('utils.dict_deep_replace')
    def test_deep_replace_dict(self, mock):
        """should call the correct function based on object type"""
        deep_object = {
            'A': 'Llfe',
            'B': 'OIFeofizejABCDEFmkfez'
        } 

        utils.deep_replace(deep_object, 'a', 'b')
        assert(mock.called)

    @patch('utils.list_deep_replace')
    def test_deep_replace_list(self, mock):
        """should call the correct function based on object type"""
        deep_object = [1, 2, 3]

        utils.deep_replace(deep_object, 'a', 'b')
        assert(mock.called)

    @patch('utils.str_deep_replace')
    def test_deep_replace_str(self, mock):
        """should call the correct function based on object type"""
        deep_object = 'test'

        utils.deep_replace(deep_object, 'a', 'b')
        assert(mock.called)

    def test_replace_host(self):
        """should return an empty string if the given textObject is an empty
        string"""
        result = utils.replace_host('', 'A', 'B')
        assert(result == '')

    @patch('traceback.print_exc')
    @patch('sys.exit')
    @patch('utils.post_box_status')
    def test_post_error_status(self, postMock, _, printExcMock):
        """should return the correct traceback and type"""
        type = 'testType'
        try:
            try:
                raise Exception('A')
            except Exception:
                raise Exception('B')
        except Exception:
            tb = traceback.format_exc()
            utils.post_error_status(type)

        expectedMessage = {
            'error_type': type,
            'error_traceback': str(tb)
        }

        postMock.assert_called_with(
            internet_connection_active=False,
            internet_connection_message=expectedMessage
            )
        printExcMock.assert_called()
