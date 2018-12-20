import git

from config import get_config_key
from config import MissingKeyInConfig
from utils import put_box_version
from utils import PutVersionError


class ApplyCommitError(Exception):
    pass


class ApplySameCommitException(Exception):
    pass


class BranchDoesNotExist(Exception):
    pass


class HeadAlreadyExists(Exception):
    pass


class RunningUpdateError(Exception):
    pass


class UpdateFetchingError(Exception):
    pass


def apply_commit(repo, commit):
    isSameCommit = str(repo.commit()) == commit
    if (isSameCommit):
        raise ApplySameCommitException(
            f'Commit {commit} is already applied.'
        )
    print("commit", commit)
    try:
        repo.git.reset(commit, '--hard')
    except Exception as e:
        raise ApplyCommitError(e)


def check_branch_exist(repo, branch):
    try:
        repo.create_head(branch, repo.remotes.origin.refs[branch])
    except AttributeError as e:
        raise BranchDoesNotExist(
            f'Failed to create the head for {branch}; {str(e)}'
        )
    except Exception as e:
        raise HeadAlreadyExists(f'Head already exists; {str(e)}')
    return True


def fetch_repo(repo):
    try:
        repo.remotes.origin.fetch()
    except Exception as e:
        raise UpdateFetchingError(f'Error while fetching github repo; {e}')


def get_last_commit(repo, branch):
    return str(repo.commit(f'origin/{branch}'))


def run_update(repoPath, config):  # noqa: C901
    repo = git.Repo(repoPath)

    print('Fetching repo...', end='')
    try:
        fetch_repo(repo)
    except UpdateFetchingError as e:
        raise RunningUpdateError(e)
    print('OK')

    print('Retrieving branch ID from config...', end='')
    try:
        branch = get_config_key(config, 'GIT_BRANCH')
    except MissingKeyInConfig as e:
        raise RunningUpdateError(e)
    print('OK')

    print('Checking if branch exists...', end='')
    try:
        check_branch_exist(repo, branch)
    except BranchDoesNotExist as e:
        raise RunningUpdateError(e)
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
    except ApplyCommitError as e:
        print('FAIL')
        raise RunningUpdateError(e)
    except ApplySameCommitException:
        print('PASS')
        print('Commit already applied.')
        return False

    print('Sending update confirmation to API...', end='')
    try:
        put_box_version(commit)
    except PutVersionError as e:
        raise RunningUpdateError(e)
    print('OK')
    return True
