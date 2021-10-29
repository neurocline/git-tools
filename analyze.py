# analyze.py
# - find git repos and analyze them

def main():
    import sys
    start_path = "."
    if len(sys.argv) > 1:
        start_path = sys.argv[1]
    scan(start_path)

def scan(base_path):
    import os
    import os.path
    import sys
    import time

    import gitlib

    status_time = time.time()

    HOOKS = 1
    INFO = 2
    OBJECTS = 4
    REFS = 8
    CONFIG = 16
    HEAD = 32
    BAREDIR = 63

    for root, dirs, files in os.walk(base_path):
        # print(f"examining {root}", file=sys.stderr)
        has_gitdir = False
        has_baredir = 0

        for d in dirs:
            if d == ".git":
                has_gitdir = True
            elif d == "hooks":
                has_baredir |= HOOKS
            elif d == "info":
                has_baredir |= INFO
            elif d == "objects":
                has_baredir |= OBJECTS
            elif d == "refs":
                has_baredir |= REFS

        for f in files:
            if f == "HEAD":
                has_baredir |= HEAD
            elif f == "config":
                has_baredir |= CONFIG

        if has_gitdir is True or has_baredir == BAREDIR:
            root_path = os.path.abspath(root).replace("\\", "/")
            # print(f"Checking potential Git repo at {root_path}")
            repo = gitlib.Git(root_path)

            analyze(repo)

            # Don't iterate inside git directory
            dirs.clear()

        if time.time() >= status_time:
            print(".", end="", file=sys.stderr, flush=True)
            status_time = time.time() + 0.1

    print(file=sys.stderr, flush=True)

repo_count = 0

def analyze(repo):
    import sys

    if repo.is_bare_repo:
        print(f"\rFound bare repo at {repo.gitdir}", file=sys.stderr, flush=True)
    elif repo.is_worktree:
        print(f"\rFound repo at {repo.gitdir}", file=sys.stderr, flush=True)
    else:
        print(f"Something wrong, not a repo at {repo.gitdir}")
        return

    global repo_count
    repo_count += 1
    print(f"[repo-{repo_count}]")

    if repo.is_worktree:
        print(f"repo = {repo.gitdir}")
    elif repo.is_bare_repo:
        print(f"bare repo = {repo.gitdir}")

    num_commits = repo.num_commits()
    print(f"commits = {num_commits}")

    branches = repo.branches()
    print(f"branches = \"{', '.join(branches)}\"")

    tags = repo.tags()
    if len(tags) > 0:
        print(f"tags = \"{', '.join(tags)}\"")

    remotes = repo.remotes()
    if len(remotes) > 0:
        print(f"remotes = \"{', '.join(remotes)}\"")

    # bare repositories don't have worktrees
    if repo.is_worktree:
        worktrees = repo.worktrees()
        if len(worktrees) > 0:
            print(f"worktrees = \"{', '.join(worktrees)}\"")

    roots = repo.roots()
    print(f"roots = \"{', '.join(roots)}\"")

    print(flush=True)

if __name__ == "__main__":
    main()
