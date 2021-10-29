# gitlib.py
# - simple wrapper around many Git commands (yes, there should be some actual Git python library)

VERBOSE = 0

class Git:
    def __init__(self, gitdir=None):
        import re

        self.gitdir = gitdir

        # test if we are inside a git worktree
        self.is_worktree = self.is_inside_worktree()

        # if we are not inside a git worktree, maybe a bare repo?
        self.is_bare_repo = False if self.is_worktree else self.is_bare_repository()

        # set up regex that we might need
        self.re_worktree = re.compile(r'(.+) ([a-fA-F0-9]{7,}) \[([^]]+)\]( prunable)?')

    def is_inside_worktree(self):
        output = self.run_git_cmd(["rev-parse", "--is-inside-work-tree"])
        if output is None:
            return False
        return output[0] == 'true'

    def is_bare_repository(self):
        output = self.run_git_cmd(["rev-parse", "--is-bare-repository"])
        if output is None:
            return False
        return output[0] == 'true'

    # --------------------------------------------------------------------------------------------

    def branches(self):
        output = self.run_git_cmd(["branch", "--list"])
        if output is None:
            return None
        branches = []
        for line in output:
            branches.append(line[2:])
        return branches

    def num_commits(self):
        return self.run_git_cmd(["rev-list", "--all", "--count"])[0]

    def remotes(self):
        output = self.run_git_cmd(["remote"])

        remotes = []
        for remote_name in output:
            remote = self.run_git_cmd(["remote", "get-url", remote_name])
            if remote is not None:
                remotes.append(f"{remote_name}:{remote[0]}")
        return remotes

    def roots(self):
        """Get roots (commits without parents)"""

        roots = []
        output = self.run_git_cmd(["rev-list", "--all", "--max-parents=0"])
        for hash in output:
            branches = []
            output_branches = self.run_git_cmd(["branch", "--contains", hash])
            if len(output_branches) > 0:
                for line in output_branches:
                    branches.append(line[2:])
            else:
                # we have no local branches, so look for remote branches owning this root
                output_branches = self.run_git_cmd(["branch", "-r", "--contains", hash])
                for line in output_branches:
                    branches.append(line[2:])
            roots.append(f"{hash}:{' '.join(branches)}")
        return roots

    def tags(self):
        return self.run_git_cmd(["tag", "--list"])

    def worktrees(self):
        import re
        import os.path

        # Don't bother to return the built-in worktree. And note that it's atypical for someone
        # to have worktrees. We'd like to know, because it's easy to lose track of them.
        output = self.run_git_cmd(["worktree", "list"])

        # The output looks like this
        # C:/projects/github/neurocline/a  f9a41f8 [main]

        worktrees = []
        for line in output:
            m = self.re_worktree.fullmatch(line)
            if m is None:
                raise RuntimeError(f"failed to match: {output}")
            worktree_path = m.group(1).rstrip()
            worktree_hash = m.group(2)
            worktree_branch = m.group(3)
            if worktree_path.lower() == os.path.abspath(self.gitdir).lower().replace("\\", "/"):
                # print(f"Skipping {worktree_path} because this is {self.gitdir}")
                pass
            else:
                worktrees.append(f"{worktree_branch}:{worktree_hash}:{worktree_path}")
        return worktrees

    # --------------------------------------------------------------------------------------------

    def run_git_cmd(self, cmd):
        import subprocess
        import sys

        git_cmd = cmd[:]
        git_cmd.insert(0, "git")
        if self.gitdir is not None:
            git_cmd.insert(1, "-C")
            git_cmd.insert(2, self.gitdir)

        if VERBOSE:
            print(git_cmd, end="", file=sys.stderr, flush=True)
        result = subprocess.run(git_cmd, capture_output=True, text=True)
        if VERBOSE:
            print("  done", file=sys.stderr, flush=True)

        self.last_stderr = result.stderr
        self.last_stdout = result.stdout
        self.returncode = result.returncode

        if self.returncode != 0:
            return None

        return self.last_stdout.splitlines()
