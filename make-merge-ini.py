# make-merge-ini.py
# - generate merge.ini from repos

def main():
    info = gather(".")
    generate(info)

def generate(info):
    # print(info)

    print("[core]")
    print("monorepo = a")

    for entry in info:
        print("")
        print(f"[repo.{entry['subtree']}]")
        print(f"source = {entry['source']}")
        print(f"subtree = {entry['subtree']}")
        print(f"main = {entry['main-branch']}")
        print(f"commits = {entry['commits']}")

        # Use the pattern ", " to separate items in a list, because space is not
        # allowed in tags, refnames (branches and remotes) or URLS (remote URLS)

        # We only need to show branches if we have more than one (singleton branches
        # are already recorded in 'main')
        if len(entry['branches']) > 1:
            print(f"branches = \"{', '.join(entry['branches'])}\"")

        if len(entry['tags']) > 0:
            print(f"tags = \"{', '.join(entry['tags'])}\"")
        if len(entry['remotes']) > 0:
            print(f"remotes = \"{', '.join(entry['remotes'])}\"")
        if len(entry['worktrees']) > 0:
            print(f"worktrees = \"{', '.join(entry['worktrees'])}\"")

        # We only need to show roots if we have more than one (a singleton root will
        # be contained in the main branch, by definition)
        if len(entry['roots']) > 1:
            print(f"roots = \"{', '.join(entry['roots'])}\"")

def gather(root):
    import os
    import os.path
    import sys

    info = []
    with os.scandir(root) as it:
        for entry in it:
            if not entry.name.startswith('.') and entry.is_dir():
                gitpath = os.path.join(root, entry.name).replace("\\", "/")
                item = gather_repo(gitpath)
                if item is not None:
                    info.append(item)
                    print(".", end="", file=sys.stderr, flush=True)
                else:
                    print(f"\nSkipping {entry.name}", file=sys.stderr, flush=True)

    print(file=sys.stderr, flush=True)
    return info

def gather_repo(gitpath):
    import os.path
    import sys

    import gitlib
    repo = gitlib.Git(gitpath)
    if not repo.is_worktree:
        print(f"Error, not worktree: {gitpath}", file=sys.stderr)
        return None

    branches = repo.branches()
    tags = repo.tags()
    remotes = repo.remotes()
    num_commits = repo.num_commits()
    worktrees = repo.worktrees()
    roots = repo.roots()

    # We will put things into a subtree that's based on the repo name
    # TBD sanitize this
    subtree = os.path.basename(gitpath)

    # Figure out what we want to call the main branch
    # - if we have "main", use it
    # - if we have "master", use it as main
    # - otherwise, use the first branch
    main_branch = None
    if 'main' in branches:
        main_branch = 'main'
    elif 'master' in branches:
        main_branch = 'master'
    else:
        main_branch = branches[0]

    item = {
        'source': gitpath,
        'subtree': subtree,
        'main-branch': main_branch,
        'branches': branches,
        'tags': tags,
        'remotes': remotes,
        'commits': num_commits,
        'worktrees': worktrees,
        'roots': roots
    }
    return item

if __name__ == "__main__":
    main()
