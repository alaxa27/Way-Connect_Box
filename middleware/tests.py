import os
import types
import traceback
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
    crons = utils.get_crons(config)

    assert(crons == [6, 9, 10])


def test_write_crons():
    """The content gets written correctly and in the right order"""
    crons = ['a', 'c']
    file = './temporary_test_file'
    utils.write_crons(crons, file)
    expectedResponse = 'a\nc\n'
    with open('./temporary_test_file', 'r') as file:
        response = file.read()
    os.remove('./temporary_test_file')
        
    assert(response == expectedResponse)



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
        print(f"Running {key}...", end=' ')
        try:
            function()
        except AssertionError:
            print(ERROR_COLOR, "FAILED", RESET_COLOR, sep='')
            errors[key] = traceback.format_exc()
        except Exception:
            print(ERROR_COLOR, "ERROR", RESET_COLOR, sep='')
            errors[key] = traceback.format_exc()
        else:
            print(SUCCESS_COLOR, "ok", RESET_COLOR, sep='')

    for key, tb in errors.items():
        print(64 * '-')
        print(f"Failure or error in {key}")
        print(64 * '-')
        print(tb)

    print(f"\nSummary: {len(tests)} tests run, {len(errors)} errors or failures.")
