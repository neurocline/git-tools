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
        print(f"main = {entry['branches'][0]}")
        print(f"commits = {entry['commits']}")

        # Use the pattern ", " to separate items in a list, because space is not
        # allowed in tags, refnames (branches and remotes) or URLS (remote URLS)
        if len(entry['branches']) > 0:
            print(f"branches = \"{', '.join(entry['branches'])}\"")
        if len(entry['tags']) > 0:
            print(f"tags = \"{', '.join(entry['tags'])}\"")
        if len(entry['remotes']) > 0:
            print(f"remotes = \"{', '.join(entry['remotes'])}\"")
        if len(entry['worktrees']) > 0:
            print(f"worktrees = \"{', '.join(entry['worktrees'])}\"")

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
                    print(f"\nSkipping {entry.name}", file=sys.stderr)

    return info

def gather_repo(gitpath):
    import os.path
    import sys

    branches = get_git_branches(gitpath)
    if branches is None:
        print(f"Error (branches): {gitpath}", file=sys.stderr)
        return None
    tags = get_git_tags(gitpath)
    remotes = get_git_remotes(gitpath)
    num_commits = get_git_num_commits(gitpath)
    worktrees = get_git_worktrees(gitpath)
    if tags is None or remotes is None or num_commits is None:
        print(f"Error (other): {gitpath}", file=sys.stderr)
        return None

    subtree = os.path.basename(gitpath)

    item = {
        'source': gitpath,
        'subtree': subtree,
        'branches': branches,
        'tags': tags,
        'remotes': remotes,
        'commits': num_commits[0],
        'worktrees': worktrees
    }
    return item

def get_git_branches(gitpath):
    output = run_get([gitpath, "branch", "--list"])
    if output is None:
        return None
    branches = []
    for line in output:
        branches.append(line[2:])
    return branches

def get_git_tags(gitpath):
    return run_get([gitpath, "tag", "--list"])

def get_git_remotes(gitpath):
    output = run_get([gitpath, "remote"])

    remotes = []
    for remote_name in output:
        remote = run_get([gitpath, "remote", "get-url", remote_name])
        if remote is not None:
            remotes.append(f"{remote_name}={remote[0]}")
    return remotes

def get_git_num_commits(gitpath):
    return run_get([gitpath, "rev-list", "--all", "--count"])

def get_git_worktrees(gitpath):
    import re
    import os.path

    # Don't bother to return the built-in worktree. And note that it's atypical for someone
    # to have worktrees. We'd like to know, because it's easy to lose track of them.
    output = run_get([gitpath, "worktree", "list"])
    re_worktree = re.compile(r'(.+) ([a-fA-F0-9]{7,}) \[([^]]+)\]( prunable)?')

    worktrees = []
    for line in output:
        m = re_worktree.fullmatch(line)
        if m is None:
            raise RuntimeError(f"failed to match: {output}")
        worktree_path = m.group(1).rstrip()
        worktree_hash = m.group(2)
        worktree_branch = m.group(3)
        if worktree_path.lower() == os.path.abspath(gitpath).lower().replace("\\", "/"):
            # print(f"Skipping {worktree_path} because this is {gitpath}")
            pass
        else:
            worktrees.append(f"{worktree_branch}:{worktree_hash}:{worktree_path}")
    return worktrees

def run_get(cmd):
    import subprocess
    cmd.insert(0, "git")
    cmd.insert(1, "-C")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return None

    return result.stdout.splitlines()

if __name__ == "__main__":
    main()
