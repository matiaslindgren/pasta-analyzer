import os
import sys
import json
import subprocess

REPOS_PATH = "cloned"
REPOS_DATA_JSON = "repo_data.json"

INDEX_DIR = os.path.join(os.path.abspath("."), "src", "backend")
sys.path.append(INDEX_DIR)
import indexer
import settings


def run_command_and_get_stdout(command, start_path=None):
    if start_path:
        previous_dir = os.path.abspath(os.curdir)
        try:
            os.chdir(start_path)
            stdout = subprocess.run(command, stdout=subprocess.PIPE, check=True).stdout
        finally:
            os.chdir(previous_dir)
    else:
        stdout = subprocess.run(command, stdout=subprocess.PIPE, check=True).stdout
    return str(stdout.strip(), 'utf-8')


def get_git_head_hash(path):
    return run_command_and_get_stdout(("git", "rev-parse", "HEAD"), path)


def get_git_root_path(repo_path):
    return run_command_and_get_stdout(("git", "rev-parse", "--show-toplevel"), repo_path)


def get_git_remote_url(blob_url, dirpath, filename):
    filepath = os.path.abspath(os.path.join(dirpath, filename))
    git_root = os.path.abspath(get_git_root_path(dirpath))
    print(filepath, git_root)
    return blob_url + "/" + os.path.relpath(filepath, git_root)


def get_current_index_size(index_path):
    command = "du -s {}".format(index_path)
    stdout = subprocess.run(command, shell=True, stdout=subprocess.PIPE, check=True).stdout
    return int(str(stdout, 'utf-8').split("\t")[0])


if __name__ == "__main__":
    index_path = os.path.join(INDEX_DIR, settings.INDEX_DIRNAME)
    if not os.path.exists(index_path):
        print("No index found at '{}', creating a new one".format(index_path))
        indexer.create_new_index(
            index_path,
            settings.INDEX_NAME,
            settings.TOKENIZER_OPTIONS
        )
    else:
        print("Found an index at '{}', appending to to the existing index".format(index_path))

    index = indexer.Index(
        index_path,
        settings.INDEX_NAME,
        settings.TOKENIZER_OPTIONS
    )

    assert os.path.exists(REPOS_PATH)
    with open(REPOS_DATA_JSON) as f:
        repos_data = json.load(f)

    for repo_number, repo in enumerate(repos_data, start=1):
        repo_name = repo['name']
        print("parse repo {} with name '{}'".format(repo_number, repo_name))

        index_current_size = get_current_index_size(index_path)
        if index_current_size > settings.INDEX_MAX_SIZE:
            print("The current size of the index is {}".format(index_current_size), file=sys.stderr)
            print("This exceeds the maximum size of {} by {}".format(settings.INDEX_MAX_SIZE, abs(index_current_size-settings.INDEX_MAX_SIZE)), file=sys.stderr)
            print("Exiting", file=sys.stderr)
            sys.exit(1)

        repo_path = os.path.join(REPOS_PATH, repo_name)
        if not os.path.exists(repo_path):
            print("non-existing repo at '{}', skipping".format(repo_path))
            continue
        git_head = get_git_head_hash(repo_path)
        blob_url = "/".join((repo["html_url"], "blob", git_head))

        print("git head is at '{}'".format(git_head))
        print("blob url '{}'".format(blob_url))

        print("parse all python files in repo '{}' at '{}'".format(repo_name, repo_path))
        valid_count = 0
        skipped_count = 0
        for dirpath, dirname, filenames in os.walk(repo_path):
            if "/.git/" in dirpath:
                continue
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if ".git" in filepath:
                    continue
                if not os.path.exists(filepath):
                    skipped_count += 1
                    continue
                with open(filepath) as f:
                    try:
                        file_contents = f.read()
                    except Exception as e:
                        skipped_count += 1
                        continue
                git_url = get_git_remote_url(blob_url, dirpath, filename)
                file_title = "{} {}".format(repo_name, filename)
                document_data = {
                    "title": file_title,
                    "url": git_url,
                    "content": file_contents}
                if not index.add_document(document_data):
                    skipped_count += 1
                else:
                    valid_count += 1
                print("{} files added to the index, {} files skipped".format(valid_count, skipped_count), end='\r')
        print()
        print("parsed and added to the index {} python files with valid syntax".format(valid_count))
        print("repo {} named '{}' done".format(repo_number, repo_name))
        print()

    print("all repos added to the index, exiting")
