import git
from pydantic import BaseModel

class Commit(BaseModel):
    short_hash: str
    hash: str
    branch: str

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
    
    def get_commits_behind(self):
        """
        Gets how many commits behind origin the current branch is.
        """
        return sum(1 for commit in self.git_repo.iter_commits("..origin"))
        
    def update(self):
        """
        Attempts to update by doing a fast-forward merge

        :return: Whether the merge was successful
        """
        status, stdout, stderr = self.git_repo.git.merge(ff_only=True, with_extended_output=True)
        return status == 0
        # TODO automatically rebuild frontend and reload backend after update
        
    def get_commit(self, ref):
        return Commit(short_hash=self.get_hash(ref, short=True), hash=self.get_hash(ref, short=False), branch=ref.name)
    
    def get_hash(self, ref = "HEAD", short = False):
        return self.git_repo.git.rev_parse(ref, short=short)
