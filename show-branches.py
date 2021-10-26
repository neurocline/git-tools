# show-branches.py
# - show branches in all repos in working directory

def main():
    find_repos(".")

def find_repos(root):
    import os
    import os.path

    with os.scandir(root) as it:
        for entry in it:
            if not entry.name.startswith('.') and entry.is_dir():
                is_git_repo(os.path.join(root, entry.name))

def is_git_repo(gitpath):
    # print(f"Checking {gitpath}")
    # Get branches. If we get an error here, then it's not a git repo
    ok, branches = get_git_branches(gitpath)
    if not ok:
        print(f"ERROR: {gitpath} is not a Git Repo")
        return

    ok, tags = get_git_tags(gitpath)
    if not ok:
        print(f"ERROR: {gitpath} is not a Git Repo")
        return

    ok, remotes = get_git_remotes(gitpath)
    if not ok:
        print(f"ERROR: {gitpath} is not a Git Repo")
        return

    # If we have remotes, then don't bother showing the ones from github:neurocline
    # (just assume it), and don't show local ones

    all_remotes = remotes[:]
    remotes = []
    for remote in all_remotes:
        if remote.find("=C:/") != -1:
            continue
        if remote.find("=../") != -1:
            continue
        if remote.find("=git@github.com:neurocline") != -1:
            continue
        remotes.append(remote)

    # print(f"{len(branches)} branches, {len(tags)} tags, {len(remotes)} all_remotes")

    if len(branches) == 0 and len(tags) == 0 and len(remotes) == 0:
        print(f"{gitpath} has no branches")
    elif len(branches) == 0 and len(remotes) == 0:
        print(f"WARNING: {gitpath} has no branches but it has tags?? {tags}")

    elif len(branches) == 1 and len(tags) == 0 and len(remotes) == 0 and branches[0] == "master":
        print(f"{gitpath} has 'master' branch")

    elif len(branches) == 1 and len(tags) == 0 and len(remotes) == 0 and branches[0] == "main":
        print(f"{gitpath} has 'main' branch")

    else:
        print(gitpath)
        print(f"  branches: {branches}")
        if len(tags) < 10:
            print(f"  tags: {tags}")
        else:
            print(f"  {len(tags)} tags: {tags[:10]}, ...")
        print(f"  remotes: {all_remotes}")

def get_git_branches(gitpath):
    import subprocess

    cmd = ["git", "-C", gitpath, "branch", "--list"]
    # print(cmd)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        # print(f"{gitpath} has branches:")
        lines = result.stdout.splitlines()
        branches = []
        for line in lines:
            # '*' means current branch
            # '+' means checked out in linked worktree
            note = line[0]
            branch = line[2:]
            # print(branch)
            branches.append(branch)

        return True, branches

    else:
        return False, []

def get_git_tags(gitpath):
    import subprocess

    cmd = ["git", "-C", gitpath, "tag", "--list"]
    # print(cmd)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        lines = result.stdout.splitlines()
        tags = []
        for tag in lines:
            tags.append(tag)

        return True, tags

    else:
        return False, []

def get_git_remotes(gitpath):
    import subprocess

    cmd = ["git", "-C", gitpath, "remote"]
    # print(cmd)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return False, []

    lines = result.stdout.splitlines()
    bare_remotes = []
    for remote in lines:
        bare_remotes.append(remote)

    # Now get the urls for the remotes
    remotes = []
    for remote in bare_remotes:
        cmd = ["git", "-C", gitpath, "remote", "get-url", remote]
        # print(cmd)
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return False, []
        lines = result.stdout.splitlines()
        remotes.append(f"{remote}={lines[0]}")

    return True, remotes

if __name__ == "__main__":
    main()
