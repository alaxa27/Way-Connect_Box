from unittest import TestCase
from unittest.mock import patch

import update


class TestUpdate(TestCase):
    @patch('git.Repo.commit')
    @patch('git.Repo')
    def test_apply_same_commit(self, repoMock, repoCommitMock):
        commitID = 'azertyuio'
        repoCommitMock.return_value = commitID
        
        # Test that ApplySameCommitException is risen
        self.assertRaises(
            update.ApplySameCommitException,
            update.apply_commit,
            repoMock,
            commitID
            )

    @patch('git.Repo.git.reset')
    @patch('git.Repo.commit')
    @patch('git.Repo')
    def test_apply_commit(self, repoMock, repoCommitMock, resetMock):
        commitID = 'ertyuikl'
        repoCommitMock.return_value = 'lkjlkjl'
        update.apply_commit(repoMock, commitID)
        # Assert that repo.git.reset is called with commitID
        resetMock.assert_called_with(commitID, '--hard')
        
