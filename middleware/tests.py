import types
import traceback


def test_success():
    assert 1 == 1


def test_failure():
    assert 1 == 2


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
