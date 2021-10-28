# merge-repos.py
# - run merge operation

def main():
    import sys
    cfg = load_config(sys.argv[1])
    run(cfg)

def load_config(inifile):
    import configparser
    import os.path

    print(f"Loading config from {inifile}")
    cfg = configparser.ConfigParser()
    cfg.read(inifile)
    return cfg

def run(cfg):
    monorepo_path = cfg['core']['monorepo']
    create_monorepo(monorepo_path)

    for section in cfg.sections():
        if section == "core":
            continue
        if cfg.has_option(section, 'enabled') and cfg.getboolean(section, 'enabled') is False:
            print(f"Skipping {section} because it is not enabled")
            continue
        source = cfg[section]['source']
        subtree = cfg[section]['subtree']
        branch = cfg[section]['main']
        add_repo(monorepo_path, source, subtree, branch)

    # At the end, do a git gc to make a single pak
    print(f"Running git gc on {monorepo_path}")
    output = run_git([monorepo_path, "gc", "--aggressive"])

def create_monorepo(gitpath):
    import os.path

    if os.path.exists(gitpath):
        raise RuntimeError(f"Not creating monorepo at {gitpath}, existing directory in the way")
    print(f"Creating monorepo at {gitpath}")
    output = run_git([".", "init", "-b", "main", gitpath])
    print(f"  creating initial commit for {gitpath}")
    output = run_git([gitpath, "commit", "--allow-empty", "-m", "Create repository"])

def add_repo(monorepo, source, subtree, branch):
    import os.path
    import shutil
    import sys

    print(f"Adding {source}:{branch} to {monorepo} as {subtree}:main")

    source_name = os.path.basename(source)

    temp_repo_name = f"a-{source_name}"
    temp_repo_dir = os.path.join(os.path.dirname(source), temp_repo_name).replace("\\", "/")
    if os.path.exists(temp_repo_dir):
        raise RuntimeError(f"Directory in the way for {temp_repo_dir}")

    # make a friendly remote name
    remote = subtree.replace("/", "_")

    print(f"  Cloning {source} into temp repo {temp_repo_dir}")
    output = run_git([".", "clone", "--no-local", source, temp_repo_dir])

    print(f"  filter-repo: moving {temp_repo_name} to {temp_repo_name}/{subtree}")
    output = run_git([temp_repo_dir, "filter-repo", "--to-subdirectory-filter", subtree, "--tag-rename", f":{subtree}-"])

    print(f"  Adding {temp_repo_dir} to {monorepo} as remotes/{remote}")
    output = run_git([monorepo, "remote", "add", "-f", remote, f"../{temp_repo_name}"])
    print(f"  Adding branch orig/{source_name}/{branch} to {monorepo}")
    output = run_git([monorepo, "branch", f"orig/{source_name}/{branch}", f"remotes/{remote}/{branch}"])

    REBASE = 1
    if REBASE:
        print(f"  Rebasing orig/{source_name}/{branch} on top of {monorepo}:main")
        output = run_git([monorepo, "rebase", "--force-rebase", "--committer-date-is-author-date", "main", f"orig/{source_name}/{branch}"])
        output = run_git([monorepo, "checkout", "main"])
        print(f"  Fast-forwarding {monorepo}:main")
        output = run_git([monorepo, "merge", "--ff-only", f"orig/{source_name}/{branch}"])
    else:
        print(f"  Merging orig/{source_name}/{branch} to {monorepo}:main")
        output = run_git([monorepo, "merge", "--allow-unrelated-histories", "--no-ff", f"orig/{source_name}/{branch}"])

    print(f"  Removing remote {remote} from {monorepo}")
    output = run_git([monorepo, "remote", "remove", remote])
    print(f"  Removing temp repo {temp_repo_dir}")
    shutil.rmtree(temp_repo_dir, ignore_errors=False, onerror=rmtree_noaccess)

def run_git(cmd):
    import subprocess

    cmd.insert(0, "git")
    cmd.insert(1, "-C")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Failed: {cmd} with {result}")

    return result.stdout.splitlines()

# use this function as a way to handle removing read only files via shutil.rmtree()
# usage example: shutil.rmtree(filename, ignore_errors=False, onerror=handle_remove_readonly)
# source: https://stackoverflow.com/questions/1213706/what-user-do-python-scripts-run-as-in-windows
def rmtree_noaccess(func, path, exc_info):
    import errno
    import os
    import stat

    exception = exc_info[1]
    if exception.errno == errno.EACCES and func in (os.rmdir, os.remove, os.unlink):
        # print(f"Remove target cannot be accessed, attempting to force via chmod 777. func={func}, path={path}")
        os.chmod(path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)  # 0777
        func(path)
    else:
        raise RuntimeError

if __name__ == "__main__":
    main()
