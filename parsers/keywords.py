"""
Parsing data into and from internal keyword representation.
"""
import re

BASEURL = "https://docs.python.org/3/library"

def url_to_keyword(url):
    if not url.startswith(BASEURL):
        raise RuntimeError("Given url '{}' does not start with '{}'".format(url, BASEURL))
    s = re.sub("({})|({})|({})".format(BASEURL, '/', '\.html'), "", url)
    if "#" in s:
        s = s.split("#")[-1]
    return s



