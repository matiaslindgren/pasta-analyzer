import os
import subprocess
import github3
import json

SEARCH_QUERY = "language:python stars:>1 size:>10000"
SEARCH_PARAMETERS = { "sort": "stars", "number": 100 }

def hard_prune_repo(repo_path):
    """Delete everything, except for *.py files and git metadata and finally remove empty folders."""
    assert os.path.exists(repo_path)
    prune_commands = (
        "find {} -type f ! -name '*.py' -not -iwholename '*.git*' -delete",
        "find {} -type d -empty -delete")
    for command in prune_commands:
        command = command.format(repo_path)
        print(command)
        subprocess.run(command, shell=True, check=True)


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


