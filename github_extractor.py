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
    command = "cloc --quiet --csv {}".format(root)
    print(command)
    result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE)
    stdout = str(result.stdout, "utf-8")
    assert "Python" in stdout
    return int(stdout.split("Python")[-1].splitlines()[0].split(",")[-1])


def count_all_repositories(root):
    assert os.path.exists(root)
    command = "find {} -type d -name '.git' | wc -l".format(root)
    print(command)
    result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE)
    return int(result.stdout.strip())


def save_metadata(cloned_destination, metadata_destination):
    assert os.path.exists(cloned_destination)
    assert os.path.exists(os.path.dirname(metadata_destination))
    python_line_count = count_all_python_lines(cloned_destination)
    repository_count = count_all_repositories(cloned_destination)
    data = {"python_line_count": python_line_count,
            "repo_count": repository_count}
    with open(metadata_destination, "w") as f:
        json.dump(data, f)
    return python_line_count, repository_count


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
    metadata_destination = os.path.join("src", "backend", "cloned_meta.json")
    print("saving meta data into '{}'".format(metadata_destination))
    python_line_count, repository_count = save_metadata(metadata_destination, cloned_destination)
    print("{} repositories at '{}'".format(repository_count, cloned_destination))
    print("containing {} lines of Python code".format(python_line_count))

