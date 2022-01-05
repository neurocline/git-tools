# analyze.py
# - find git repos and analyze them

SHOW_GIT_IGNORE = 0

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
            start_time = time.time()
            root_path = os.path.abspath(root).replace("\\", "/")
            # print(f"Checking potential Git repo at {root_path}")
            repo = gitlib.Git(root_path)

            analyze(repo)
            delta_time = time.time() - start_time
            print(f"elapsed = {delta_time:.3f}")

            print(flush=True)

            # Don't iterate inside git directory
            dirs.clear()

        if time.time() >= status_time:
            print(".", end="", file=sys.stderr, flush=True)
            status_time = time.time() + 0.1

    print(file=sys.stderr, flush=True)

repo_count = 0

def analyze(repo):
    import sys
    import time

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

    # Calculate repo signature (TBD: will use this to know if a repo has changed
    # since the last time we looked at it).
    start_time = time.time()
    signature = repo.signature()
    delta_time = time.time() - start_time
    print(f"signature = {signature} ({delta_time:.3f})")

    print(f"repo = {repo.gitdir}")
    if repo.is_bare_repo:
        print(f"bare = true")

    num_commits = repo.num_commits()
    print(f"commits = {num_commits}")

    # we can't get the last commit date if there are no commits
    if num_commits > 0:
        last_commit_date = repo.last_commit_date()
        print(f"last_commit = {last_commit_date}")

    object_stats = repo.count_objects()
    num_loose = object_stats.get('count', 0)
    if num_loose > 0:
        print(f"loose = {num_loose} ({object_stats.get('size', 0)} KB)")
    num_garbage = object_stats.get('garbage', 0)
    if num_garbage > 0:
        print(f"garbage = {num_garbage} ({object_stats.get('size-garbage', 0)} KB)")
    num_packs = object_stats.get('packs', 0)
    if num_packs > 0:
        print(f"packs = {num_packs}/{object_stats.get('in-pack', 0)} ({object_stats.get('size-pack', 0)} KB)")

    branches = repo.branches()
    print(f"branches = \"{', '.join(branches)}\"")

    # Figure out what we want to call the main branch
    # - if we have "main", use it
    # - if we have "master", use it as main
    # - otherwise, use the first branch
    repo.main_branch = None
    if len(branches) > 0:
        if 'main' in branches:
            repo.main_branch = 'main'
        elif 'master' in branches:
            repo.main_branch = 'master'
        else:
            repo.main_branch = branches[0]

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

    # Apparently we can only issue "git submodule" calls in working trees. Even though
    # bare git trees can have submodules, they can't really be used, because most of the
    # point of a submodule is to fetch files into the worktree
    if repo.is_worktree:
        submodules = repo.submodules()
        if submodules is not None and len(submodules) > 0:
            print(f"submodules = \"{', '.join(submodules)}\"")

    roots = repo.roots()
    print(f"roots = \"{', '.join(roots)}\"")

    hooks = repo.hooks()
    if len(hooks) > 0:
        print(f"hooks = \"{', '.join(hooks)}\"")

    # show uncommitted files (TBD to show ignores as well)
    # We can only do this on worktrees (TBD to do it on all worktrees)
    if repo.is_worktree:
        uncommitted = repo.uncommitted()
        if len(uncommitted) > 0:
            print(f"uncommitted = \"{', '.join(uncommitted)}\"")

    # show refs not merged to main
    # (very little point on doing this for bare repos)
    if repo.main_branch is not None and not repo.is_bare_repo:
        unmerged = repo.unmerged()
        if len(unmerged) > 0:
            print(f"unmerged = {len(unmerged)} commits")

    # Show local commits not pushed to tracking branches
    # (no point on doing this for bare repositories)
    if not repo.is_bare_repo:
        unpushed = repo.unpushed()
        if len(unpushed) > 0:
            print(f"unpushed = {len(unpushed[0])} branches with {len(unpushed[1])} commits")

    # Show stashed commits (bare repos could have stashes, but won't, in reality)
    stashes = repo.stashes()
    if len(stashes) > 0:
        flat_stashes = '\\n'.join(stashes)
        print(f"stashes = \"{flat_stashes}\"")

    # See if we have a .gitignore at the root of the repo
    if SHOW_GIT_IGNORE:
        gitignore_data = repo.read_gitignore()
        if gitignore_data is not None:
            flat_gitignore = '\\n'.join(gitignore_data)
            print(f"gitignore = \"{flat_gitignore}\"")

if __name__ == "__main__":
    main()
