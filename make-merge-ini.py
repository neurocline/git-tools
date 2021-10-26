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
        print(f"[repo-{entry['subtree']}]")
        print(f"source = {entry['source']}")
        print(f"subtree = {entry['subtree']}")
        print(f"main = {entry['branches'][0]}")

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

    branches = get_git_branches(gitpath)
    tags = get_git_tags(gitpath)
    if branches is None or tags is None:
        return None

    #if len(branches) != 1:
    #    return None
    #if len(tags) != 0:
    #    return None

    subtree = os.path.basename(gitpath)

    item = {
        'source': gitpath,
        'subtree': subtree,
        'branches': branches,
        'tags': tags
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
