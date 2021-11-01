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

        # Some information we cache
        self.main_branch = None

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
        branches_report = []
        for line in output:
            branches_report.append(line[2:])
        return branches_report

    def last_commit_date(self):
        output = self.run_git_cmd(["log", "--all", "-1", "--date-order", "--format=format:%cs"])
        if output is None or len(output) == 0:
            return None
        return output[0]

    def num_commits(self):
        return int(self.run_git_cmd(["rev-list", "--all", "--count"])[0])

    def count_objects(self):
        output = self.run_git_cmd(["count-objects", "-v"])
        # count: 4356
        # size: 90642
        # in-pack: 309
        # packs: 1
        # size-pack: 132508
        # prune-packable: 0
        # garbage: 0
        # size-garbage: 0
        stats = dict()
        for line in output:
            label, value = line.split(": ")
            stats[label] = int(value)
        return stats

    def hooks(self):
        import os
        import os.path
        import sys

        # https://git-scm.com/docs/githooks
        git_am_hooks = ['applypatch-msg', 'pre-applypatch', 'post-applypatch']
        git_checkout_hooks = ['post-checkout']
        git_commit_hooks = ['pre-commit', 'prepare-commit-msg', 'commit-msg', 'post-commit']
        git_fsmonitor_hooks = ['fsmonitor-watchman']
        git_gc_hooks = ['pre-auto-gc']
        git_index_write_hooks = ['post-index-change']
        git_merge_hooks = ['pre-merge-commit', 'commit-msg', 'post-merge']
        git_p4_hooks = ['p4-changelist', 'p4-prepare-changelist', 'p4-post-changelist', 'p4-pre-submit']
        git_push_hooks = ['pre-push']
        git_receive_pack_hooks = ['pre-receive', 'update', 'proc-receive', 'post-receive', 'post-update', 'push-to-checkout']
        git_rebase_hooks = ['pre-rebase']
        git_reference_hooks = ['reference-transaction']
        git_rewrite_commits_hooks = ['post-rewrite']
        git_send_email_hooks = ['sendemail-validate']

        git_hooks = [
            *git_am_hooks, *git_checkout_hooks, *git_commit_hooks, *git_fsmonitor_hooks,
            *git_gc_hooks, *git_index_write_hooks, *git_merge_hooks, *git_p4_hooks, *git_push_hooks,
            *git_receive_pack_hooks, *git_rebase_hooks, *git_reference_hooks,
            *git_rewrite_commits_hooks, *git_send_email_hooks]

        hooks_report = []
        if self.is_bare_repo:
            hooks_path = os.path.join(self.gitdir, "hooks")
        else:
            hooks_path = os.path.join(self.gitdir, ".git", "hooks")

        # print(f"Searching {hooks_path}:", file=sys.stderr, flush=True)
        for root, dirs, files in os.walk(hooks_path):
            # there should not be any directories here
            for d in dirs:
                print(f"Hook dir?! {d}", file=sys.stderr, flush=True)
                hooks_report.append(f"Hook dir d")
            dirs.clear()

            for f in files:
                if f.lower().endswith(".sample"):
                    f = f[:-7] #  need 3.9 for f = f.removesuffix(".sample")
                    if f.lower() not in git_hooks:
                        hooks_report.append(f"Nonstandard {f}.sample")
                else:
                    if f.lower() not in git_hooks:
                        hooks_report.append(f"Nonstandard hook {f}")
                    else:
                        hooks_report.append(f"Hook {f}")
        return hooks_report

    def remotes(self):
        output = self.run_git_cmd(["remote"])

        remotes_report = []
        for remote_name in output:
            remote = self.run_git_cmd(["remote", "get-url", remote_name])
            if remote is not None:
                remotes_report.append(f"{remote_name}:{remote[0]}")
        return remotes_report

    def roots(self):
        """Get roots (commits without parents)"""

        roots_report = []
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
            roots_report.append(f"{hash}:{' '.join(branches)}")
        return roots_report

    def tags(self):
        return self.run_git_cmd(["tag", "--list"])

    def uncommitted(self):
        output = self.run_git_cmd(["status", "-s"])
        uncommitted_report = []
        for line in output:
            uncommitted_report.append(line)
        return uncommitted_report

    def unmerged(self):
        if self.main_branch is None:
            return 0
        output = self.run_git_cmd(["log", "--all", "--format=format:%H", "--not", self.main_branch])
        return output

    def worktrees(self):
        import re
        import os.path

        # Don't bother to return the built-in worktree. And note that it's atypical for someone
        # to have worktrees. We'd like to know, because it's easy to lose track of them.
        output = self.run_git_cmd(["worktree", "list"])

        # The output looks like this
        # C:/projects/github/neurocline/a  f9a41f8 [main]

        worktrees_report = []
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
                worktrees_report.append(f"{worktree_branch}:{worktree_hash}:{worktree_path}")
        return worktrees_report

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
