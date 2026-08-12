import os
import shutil
import tempfile
import subprocess
from typing import Tuple, Optional

def resolve_repo_path(raw_path: str) -> Tuple[str, Optional[str], str]:
    """
    Resolves raw_path. If raw_path is a Git URL (GitHub, GHE, GitLab, etc.),
    clones it to a temporary directory and returns (local_abspath, temp_dir_for_cleanup, repo_name).
    Otherwise returns (local_abspath, None, repo_name).
    """
    if not raw_path:
        raw_path = "."
        
    raw_path = raw_path.strip()
    
    is_url = (
        raw_path.startswith(("http://", "https://", "git@")) or
        "github.com" in raw_path or
        "gitlab.com" in raw_path or
        raw_path.endswith(".git")
    )
    
    if is_url:
        url = raw_path
        if url.startswith("github.com/"):
            url = "https://" + url
        elif url.startswith("gitlab.com/"):
            url = "https://" + url

        repo_name = url.rstrip("/").split("/")[-1].replace(".git", "")
        temp_dir = tempfile.mkdtemp(prefix="docu_compress_repo_")
        
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", url, temp_dir],
                check=True,
                capture_output=True,
                text=True
            )
            return temp_dir, temp_dir, repo_name
        except subprocess.CalledProcessError as e:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
            stderr_msg = e.stderr.strip() if e.stderr else str(e)
            raise RuntimeError(f"Failed to clone Git repository from '{url}': {stderr_msg}")
        except Exception as e:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
            raise RuntimeError(f"Failed to clone repository from '{url}': {str(e)}")
            
    abs_path = os.path.abspath(raw_path)
    repo_name = os.path.basename(abs_path) or abs_path
    return abs_path, None, repo_name
