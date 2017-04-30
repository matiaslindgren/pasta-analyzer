"""
Scrapy spider for crawling all links on the python docs library page
TODO:
 - scrap LINK_CACHE and use some external service such as redis
"""
import scrapy
import collections
import re


class PATTERN:
    TOCTREE_LINKS = "//ul/li[contains(@class, 'toctree')]/a"
    PAGE_SECTIONS = "//div[contains(@class, 'section')]/dl"
    HREF = ".//@href"
    SECTION_LINKS = ".//dt/a[contains(@class, 'headerlink')]/@href"
    INTERNAL_LINKS = ".//dd//a[contains(@class, 'internal reference') or contains(@class, 'reference internal')]/@href"
    TEXT = ".//text()"
    SHELL_STRINGS = (
        ">>>",
        "...",
    )
    # REFERENCE
    # div class=section id='name'
    #   p p p
    #

def parse_highlighted_code(selector):
    def contains_shell_characters(string):
        shell_pattern = re.compile("|".join("^" + re.escape(p) for p in PATTERN.SHELL_STRINGS))
        return re.search(shell_pattern, string) is not None
    code_text = selector.xpath(PATTERN.TEXT).extract()
    return ''.join(s for s in code_text if not contains_shell_characters(s))


class DocSpider(scrapy.Spider):
    name = "docs"
    start_urls = (
        # 'http://docs.python.org/3/library',
        # 'http://docs.python.org/3/reference',
        'localhost:8000/reference',
    )
    LINK_CACHE = collections.defaultdict(set)

    def parse(self, response):
        self.logger.debug("Parsing response {}".format(response))
        for page in response.xpath(PATTERN.TOCTREE_LINKS):
            next_url = response.urljoin(page.xpath(PATTERN.HREF).extract_first())
            self.logger.debug("Requesting {}".format(next_url))
            yield scrapy.Request(next_url, self.parse_page)

    def parse_page(self, response):
        self.logger.debug("Parsing page {}".format(response))
        for section in response.xpath(PATTERN.PAGE_SECTIONS):
            # print("parsing section {}".format(section))
            section_name = section.xpath(PATTERN.HREF).extract_first()
            # print("section_name {}".format(section_name), end=';')
            section_url = section.xpath(PATTERN.SECTION_LINKS).extract_first()
            internal_links = section.xpath(PATTERN.INTERNAL_LINKS).extract()
            self.store_edges(
                response.urljoin(section_url),
                map(response.urljoin, internal_links)
            )

    def store_edges(self, from_url, to_urls):
        self.__class__.LINK_CACHE[from_url]
        for url in to_urls:
            self.__class__.LINK_CACHE[from_url].add(url)


class WriterPipeline:
    def close_spider(self, spider):
        spider.logger.debug("Closing spider {}".format(spider))
        with open("out", "w") as f:
            spider.logger.debug("Writing output from cache, which has {} items".format(len(DocSpider.LINK_CACHE)))
            for from_url, to_urls in DocSpider.LINK_CACHE.items():
                f.write(from_url + ";" + ",".join(to_urls) + "\n")



