import os
import shutil
import subprocess
import json
import sys


start_path = os.path.abspath(".")

spiders = ("tutorial", "library")
data_dir = os.path.join(start_path, "src", "backend")
data_path = os.path.join(data_dir, "data.json")
scrapy_path = os.path.join(start_path, "src", "scraper")

sys.path.append(data_dir)
import indexer
import settings


def spider_output_path(spider):
    return os.path.join(data_dir, "{}_out.json".format(spider))

if os.path.exists(data_path):
    print("Previous crawl output exists, removing {}".format(data_path))
    os.remove(data_path)

os.chdir(scrapy_path)
for spider_name in spiders:
    command = (
        "scrapy", "crawl", spider_name, "-o", spider_output_path(spider_name),
        "--logfile", "scrapy.log"
    )
    print("Crawl with spider '{}'".format(spider_name))
    subprocess.run(command, check=True)
os.chdir(start_path)

print("Crawling complete, joining crawl output")
scraped_data = []
for output in map(spider_output_path, spiders):
    with open(output) as f:
        scraped_data.extend(json.load(f))
    os.remove(output)

index_path = os.path.join(start_path, data_dir, settings.INDEX_DIRNAME)
print("Building index")
if os.path.exists(index_path):
    print("Previous index exists, removing {}".format(index_path))
    shutil.rmtree(index_path)

print("Create index")
indexer.create_new_index(
    index_path,
    settings.INDEX_NAME,
    settings.TOKENIZER_OPTIONS
)

print("Add crawled output to index")
index = indexer.Index(
    index_path,
    settings.INDEX_NAME,
    settings.TOKENIZER_OPTIONS
)
for data in scraped_data:
    index.add_documents(data)

print("All done")


