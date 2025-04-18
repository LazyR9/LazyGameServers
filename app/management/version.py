from typing import Any
import git
from pydantic import BaseModel

class Commit(BaseModel):
    short_hash: str
    hash: str

# TODO handle behind ahead of origin, tho it should only happen in development
class VersionManager:
    def __init__(self, repo_path = "."):
        self.git_repo = git.Repo(repo_path)
        
    def check_for_updates(self):
        """
        Runs a `git fetch` to see what changes have been made.
        Use `update()` to try and apply them.

        :return: How many commits behind origin we are
        """
        self.git_repo.remote().fetch()
        return self.get_commits_behind()
    
    def get_commits_behind(self, branch = None):
        """
        Gets how many commits behind origin `branch` is.
        
        :param branch: Branch to check, or `None` to check the active branch.
        :return: The number of commits between the local branch and the remote branch 
        """
        if branch is None:
            branch = self.git_repo.active_branch
        return sum(1 for commit in self.git_repo.iter_commits(f"{branch}..origin/{branch}"))
        
    def update(self):
        """
        Attempts to update by doing a fast-forward merge

        :return: Whether the merge was successful
        """
        status, stdout, stderr = self.git_repo.git.merge(ff_only=True, with_extended_output=True)
        return status == 0
        # TODO automatically rebuild frontend and reload backend after update
        
    def get_commit(self, ref: Any):
        """
        Gets a `Commit` object representing the commit at `ref`

        :param ref: Reference to get the `Commit` object for.
            Can be a string, or an object that returns a valid git reference in its __str__() method
            (like a git python object)
        :return: The found `Commit` object
        """
        return Commit(short_hash=self.get_hash(ref, short=True), hash=self.get_hash(ref, short=False))
    
    def get_hash(self, ref: Any = "HEAD", short = False) -> str:
        """
        Gets the hash of a reference

        :param ref: Reference to get, defaults to "HEAD".
            Can be a string, or an object that returns a valid git reference in its __str__() method
            (like a git python object)
        :param short: Whether to get the full hash, or the shortened one. defaults to False
        :return: The reference hash
        """
        return self.git_repo.git.rev_parse(ref, short=short)
