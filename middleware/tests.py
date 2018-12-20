from unittest.mock import patch
import os
import types
import sys
import traceback

import crontab
import utils


def test_get_crons():
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


def test_write_crons():
    """The content gets written correctly and in the right order"""
    crons = ['a', 'c']
    file = './temporary_test_file'
    crontab.write_crons(crons, file)
    expectedResponse = 'a\nc\n'
    with open('./temporary_test_file', 'r') as file:
        response = file.read()
    os.remove('./temporary_test_file')
        
    assert(response == expectedResponse)


def test_str_deep_replace():
    """Dumb string.replace; it should always respect the occurence"""
    occ = 'LKJfezFE'
    result = utils.str_deep_replace('OIEFHAOFHoIJfeozij', occ, 'test')
    assert('test' not in result)
    result = utils.str_deep_replace('OIEFHALKJfezFEOFHoIJfeozij', occ, 'test')
    assert('test' in result)


def test_list_deep_replace():
    """It should replace the strings with the given occurrence in an array"""
    occ = 'MLKMLK'
    deep_list = ['aziufoiea', 'lkfajekfjMLKMLKdzahfi']
    result = utils.list_deep_replace(deep_list, occ, 'test')

    assert('test' not in result[0])
    assert('test' in result[1])


def test_dict_deep_replace():
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
def test_deep_replace_dict(mock):
    """should call the correct function based on object type"""
    deep_object = {
        'A': 'Llfe',
        'B': 'OIFeofizejABCDEFmkfez'
    } 

    utils.deep_replace(deep_object, 'a', 'b')
    assert(mock.called)


@patch('utils.list_deep_replace')
def test_deep_replace_list(mock):
    """should call the correct function based on object type"""
    deep_object = [1, 2, 3]

    utils.deep_replace(deep_object, 'a', 'b')
    assert(mock.called)


@patch('utils.str_deep_replace')
def test_deep_replace_str(mock):
    """should call the correct function based on object type"""
    deep_object = 'test'

    utils.deep_replace(deep_object, 'a', 'b')
    assert(mock.called)


def test_replace_host():
    """should return an empty string if the given textObject is an empty string"""
    result = utils.replace_host('', 'A', 'B')
    assert(result == '')


@patch('sys.exit')
@patch('utils.post_box_status')
def test_post_error_status(mock, _):
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

    mock.assert_called_with(
        internet_connection_active=False,
        internet_connection_message=expectedMessage
        )


if __name__ == '__main__':
    SUCCESS_COLOR = '\033[92m'
    ERROR_COLOR = '\033[91m'
    RESET_COLOR = '\033[0m'

    err = None
    tests = {
        k: v for k, v in locals().items()
        if isinstance(v, types.FunctionType) and k.startswith('test_')
    }
    errors = {}
    for key, function in tests.items():
        print(f'Running {key}...', end=' ')
        try:
            function()
        except AssertionError:
            print(ERROR_COLOR, 'FAILED', RESET_COLOR, sep='')
            errors[key] = traceback.format_exc()
        except Exception:
            print(ERROR_COLOR, 'ERROR', RESET_COLOR, sep='')
            errors[key] = traceback.format_exc()
        else:
            print(SUCCESS_COLOR, 'ok', RESET_COLOR, sep='')

    for key, tb in errors.items():
        print(64 * '-')
        print(f'Failure or error in {key}')
        print(64 * '-')
        print(tb)

    print(f'\nSummary: {len(tests)} tests run, {len(errors)} errors or failures.')
