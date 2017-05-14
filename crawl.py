import os
import subprocess
import json


start_path = os.path.abspath(".")

spiders = ("tutorial", "library")
data_dir = os.path.join(start_path, "src", "backend")
data_path = os.path.join(data_dir, "data.json")
scrapy_path = os.path.join(start_path, "src", "scraper")

def spider_output_path(spider):
    return os.path.join(data_dir, "{}_out.json".format(spider))

if os.path.exists(os.path.join(data_path, "data.json")):
    print("previous crawl output exists, removing {}".format(data_path))
    os.remove(data_path)

os.chdir(scrapy_path)
for spider_name in spiders:
    command = (
        "scrapy", "crawl", spider_name, "-o", spider_output_path(spider_name)
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
with open(data_path, "w") as f:
    json.dump(scraped_data, f)

print("All done")


