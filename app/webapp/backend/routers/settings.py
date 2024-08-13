from fastapi import APIRouter
from pydantic import BaseModel

from app.management.version import Commit

from ..dependencies import ManagerDependency

    
class VersionInfo(BaseModel):
    current: Commit
    latest: Commit
    commits_behind: int


router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/version")
def get_version(manager: ManagerDependency):
    version = manager.version_manager
    ref = version.git_repo.head.ref
    return VersionInfo(current=version.get_commit(ref), latest=version.get_commit(ref.tracking_branch()), commits_behind=version.get_commits_behind())

@router.post("/version/check")
def check_for_updates(manager: ManagerDependency):
    # TODO check_for_updates() calls get_commits_behind() but so does get_version(), so it is called twice
    manager.version_manager.check_for_updates()
    return get_version(manager)

@router.post("/version/update")
def update(manager: ManagerDependency):
    return {"success": manager.version_manager.update()}

