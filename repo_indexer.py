import os
import sys
import json
import subprocess
import shutil

REPOS_PATH = "cloned"
REPOS_DATA_JSON = "repo_data.json"

INDEX_DIR = os.path.join(os.path.abspath("."), "src", "backend")
sys.path.append(INDEX_DIR)
import indexer
import settings


def get_command_result(args):
    stdout = subprocess.run(args, stdout=subprocess.PIPE, check=True).stdout
    return str(stdout, 'utf-8').strip()


if __name__ == "__main__":
    index_path = os.path.join(INDEX_DIR, settings.INDEX_DIRNAME)
    if os.path.exists(index_path):
        print("Previous index exists, removing {}".format(index_path))
        shutil.rmtree(index_path)

    print("Create index")
    indexer.create_new_index(
        index_path,
        settings.INDEX_NAME,
        settings.TOKENIZER_OPTIONS
    )
    index = indexer.Index(
        index_path,
        settings.INDEX_NAME,
        settings.TOKENIZER_OPTIONS
    )
    assert os.path.exists(REPOS_PATH)
    get_head = ["git", "rev-parse", "HEAD"]
    with open(REPOS_DATA_JSON) as f:
        repos_data = json.load(f)
    for repo in repos_data[2:]:
        repo_name = repo['name']
        repo_path = os.path.join(REPOS_PATH, repo_name)
        if not os.path.exists(repo_path):
            print("skip non-existing repo '{}'".format(repo_path))
            continue
        previous_dir = os.path.abspath(os.curdir)
        os.chdir(repo_path)
        git_head = get_command_result(get_head)
        print("processing repo '{}'".format(os.path.abspath(os.curdir)))
        print("git head is at '{}'".format(git_head))
        blob_url = "/".join((repo["html_url"], "blob", git_head))
        print("blob url '{}'".format(blob_url))
        valid_count = 0
        skipped_count = 0
        for dirpath, dirname, filenames in os.walk('.'):
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
                if filepath.startswith("./"):
                    url_filepath = filepath[2:]
                git_url = blob_url + "/" + url_filepath
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
        print("repo has {} files with valid python syntax".format(valid_count))
        os.chdir(previous_dir)
        print()

