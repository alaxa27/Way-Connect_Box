from dotenv import load_dotenv
import git
import os
from pathlib import Path
import requests
import sys

from config import get_config_key
from config import MissingKeyInConfig
from utils import sign


class ApplyCommitError(Exception):
    pass


class ApplySameCommitException(Exception):
    pass


class BranchDoesNotExist(Exception):
    pass


class HeadAlreadyExists(Exception):
    pass


class PutVersionError(Exception):
    pass


class RunUpdateError(Exception):
    pass


class RerunScriptError(Exception):
    pass


class UpdateFetchingError(Exception):
    pass


def apply_commit(repo, commit):
    isSameCommit = str(repo.commit()) == commit
    if (isSameCommit):
        raise ApplySameCommitException()
    try:
        repo.git.reset(commit, '--hard')
    except Exception:
        raise ApplyCommitError()


def check_branch_exist(repo, branch):
    try:
        repo.create_head(branch, repo.remotes.origin.refs[branch])
    except AttributeError:
        raise BranchDoesNotExist()
    except Exception:
        raise HeadAlreadyExists()
    return True


def fetch_repo(repo):
    try:
        repo.remotes.origin.fetch()
    except Exception:
        raise UpdateFetchingError()


def get_last_commit(repo, branch):
    return str(repo.commit(f'origin/{branch}'))


def put_box_version(version):
    envPath = Path('/home/pi')
    load_dotenv(dotenv_path=envPath / 'env', override=True)
    API_HOST = os.environ['API_HOST']
    API_KEY = os.environ['API_KEY']
    API_SECRET = os.environ['API_SECRET']

    boxVersion = {}
    boxVersion['commit_hash'] = version

    signature = sign(API_KEY, API_SECRET, boxVersion)

    headers = {}
    headers['Host'] = API_HOST
    headers['X-API-Key'] = API_KEY
    headers['X-API-Sign'] = signature

    response = requests.put(
        url=f'http://{API_HOST}/boxes/version/',
        json=boxVersion,
        headers=headers
    )
    try:
        response.raise_for_status()
    except requests.HTTPError:
        raise PutVersionError(version)


def rerun_script(repoPath):
    scriptPath = f'{repoPath}/middleware/recurrent_tasks.py'
    try:
        os.execv(scriptPath, sys.argv + ['--update-config', '--reboot'])
    except OSError:
        raise RerunScriptError()


def run_update(repoPath, config):  # noqa: C901
    repo = git.Repo(repoPath)

    print('Fetching repo...', end='')
    try:
        fetch_repo(repo)
    except UpdateFetchingError:
        raise RunUpdateError()
    print('OK')

    print('Retrieving branch ID from config...', end='')
    try:
        branch = get_config_key(config, 'GIT_BRANCH')
    except MissingKeyInConfig:
        raise RunUpdateError()
    print('OK')

    print('Checking if branch exists...', end='')
    try:
        check_branch_exist(repo, branch)
    except BranchDoesNotExist:
        print('FAIL')
        raise RunUpdateError()
    except HeadAlreadyExists:
        pass
    print('OK')

    print('Retrieving commit ID from config...', end='')
    try:
        commit = get_config_key(config, 'GIT_COMMIT')
        print('OK')
    except MissingKeyInConfig:
        print('FAIL')
        print('Retrieving commit ID from last branch commit...', end='')
        commit = get_last_commit(repo, branch)
        print('OK')

    print(f'Applying commit {commit}...', end='')
    try:
        apply_commit(repo, commit)
    except ApplyCommitError:
        print('FAIL')
        raise RunUpdateError()
    except ApplySameCommitException:
        print('PASS')
        print('Commit already applied.')
        return False

    print('Sending update confirmation to API...', end='')
    try:
        put_box_version(commit)
    except PutVersionError:
        print('FAIL')
        raise RunUpdateError()
    print('OK')

    print('---> Running latest recurrent tasks:')
    try:
        rerun_script(repoPath)
    except RerunScriptError:
        print('---> Failed to run latest recurrent tasks.')
        raise RunUpdateError()
