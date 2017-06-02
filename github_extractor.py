import os
import subprocess
import github3
import json

SEARCH_QUERY = "language:python stars:>1 size:>10000"
SEARCH_PARAMETERS = { "sort": "stars", "number": 100 }


def hard_prune_repo(repo_path):
    """
    1. Delete all files, except git metadata and files with names that match *.py.
    2. Delete all empty folders.
    3. Delete all symbolic links.
    4. Set permission for all files to 440.
    """
    assert os.path.exists(repo_path)
    prune_commands = (
        "find {} -type f ! -name '*.py' -not -iwholename '*.git*' -delete",
        "find {} -type d -empty -delete",
        "find {} -type l -delete",
        "find {} -type f -exec chmod 440 {{}} \;")
    for command in prune_commands:
        command = command.format(repo_path)
        print(command)
        subprocess.run(command, shell=True, check=True)


def count_all_python_lines(root):
    """
    Run CLOC at root and return the amount of lines of Python code in every file.
    """
    assert os.path.exists(root)
    command = "cloc --quiet --csv {}".format(root).format(repo_path)
    print(command)
    result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE)
    stdout = str(result.stdout, "utf-8")
    assert "Python" in stdout
    return int(stdout.split("Python")[-1].splitlines()[0].split(",")[-1])


if __name__ == "__main__":
    repo_data_file = os.path.join(".", "repo_data.json")

    repos = None
    if not os.path.exists(repo_data_file):
        print("updating repo data into '{}'".format(repo_data_file))
        with open("repo_data.json", "w") as f:
            repo_iterator = github3.search_repositories(
                    SEARCH_QUERY,
                    **SEARCH_PARAMETERS)
            repos = [repo.to_json() for repo in repo_iterator]
            json.dump(repos, f)
    else:
        print("not updating existing repo data at '{}'".format(repo_data_file))
        with open("repo_data.json") as f:
            repos = json.load(f)

    cloned_destination = os.path.join(".", "cloned")
    if not os.path.exists(cloned_destination):
        print("create '{}'".format(cloned_destination))
        os.mkdir(cloned_destination)
    else:
        print("not creating existing '{}'".format(cloned_destination))

    print("cloning {} repos".format(len(repos)))
    for repo in repos:
        repo_path = os.path.join(cloned_destination, repo["name"])
        if not os.path.exists(repo_path):
            command = ["git", "clone", repo["clone_url"], repo_path]
            print(" ".join(command))
            subprocess.run(command, check=True)
            print()
            print("pruning repo from all non python files")
            hard_prune_repo(repo_path)
            print()
        else:
            print("not cloning into existing '{}'".format(repo_path))

    print()
    print("all repos cloned")
    print("counting amount of Python lines in '{}'".format(cloned_destination))
    python_line_count = count_all_python_lines(cloned_destination)
    cloned_meta = os.path.join(cloned_destination, "meta.json")
    print("{} lines of Python code, saving result to '{}'".format(python_line_count, cloned_meta))
    with open("meta.json", "w") as f:
        json.dump({"python_line_count": python_line_count}, f)

