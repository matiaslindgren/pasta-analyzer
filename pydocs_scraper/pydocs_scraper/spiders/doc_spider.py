"""
Scrapy spiders for crawling the Python docs.
"""
import scrapy
import re


class PATTERN:
    """
    XPath selectors and other string constants.
    """
    _SECTION_DIV         = "div[contains(@class, 'section')]"
    ALL_PAGE_SECTIONS    = ".//" + _SECTION_DIV
    CHILD_PAGE_SECTIONS  = "./" + _SECTION_DIV
    LIST_PAGE_SECTIONS   = "./{}/dl".format(_SECTION_DIV)
    TOCTREE_TOP_LINKS    = "//ul/li[contains(@class, 'toctree-l1')]/a"
    SECTION_LINKS        = ".//dt/a[contains(@class, 'headerlink')]/@href"
    HEADER_SECTION_LINKS = "|".join("(.//h{}/a[contains(@class, 'headerlink')]/@href)".format(i) for i in range(1, 5))
    INTERNAL_LINKS       = ".//dd//a[contains(@class, 'internal reference') or contains(@class, 'reference internal')]/@href"
    CHILD_CODE_SNIPPETS  = "./div[contains(@class, 'highlight-python3')]"
    HREF                 = ".//@href"
    ALL_TEXT             = ".//text()"
    SHELL_STRINGS        = (
        ">>>",
        "...",
    )


def parse_highlighted_code(snippet_selector):
    """
    Return the html highlighted code selected by the scrapy.Selector given as parameter as a plain string without shell characters.
    """
    def no_shell_characters_in(string):
        shell_pattern = re.compile("|".join("^" + re.escape(p) for p in PATTERN.SHELL_STRINGS))
        return re.search(shell_pattern, string) is None
    unhighlighted_code_pieces = snippet_selector.xpath(PATTERN.ALL_TEXT).extract()
    return ''.join(filter(no_shell_characters_in, unhighlighted_code_pieces))


class TutorialSpider(scrapy.Spider):
    name = "tutorial"
    start_urls = (
        # 'http://docs.python.org/3/tutorial',
        'http://localhost:8000/tutorial',
    )

    def parse(self, response):
        self.logger.debug("Parsing response {}".format(response))
        for page in response.xpath(PATTERN.TOCTREE_TOP_LINKS):
            next_url = response.urljoin(page.xpath(PATTERN.HREF).extract_first())
            yield scrapy.Request(next_url, self.parse_page)

    def parse_page(self, page):
        """
        Helper method for starting the parse of all sections on 'page' from the root section.
        """
        self.logger.debug("Parsing page {}".format(page))
        sections = page.xpath(PATTERN.ALL_PAGE_SECTIONS)
        if not sections:
            self.logger.warning("Page has no parsable sections")
            return None
        yield from self.parse_section(sections[0])

    def parse_section(self, section):
        """
        Recursively yield dicts of url string and code snippets list within 'section' and all its nested sections.
        The data within a nested section is not included into the data of its parent, unless it is explicitly duplicate in the html.
        """
        def get_section_url(s):
            return s.xpath(PATTERN.HEADER_SECTION_LINKS).extract_first()
        section_url = get_section_url(section)
        self.logger.debug("Parsing section {}".format(section_url))
        for subsection in section.xpath(PATTERN.CHILD_PAGE_SECTIONS):
            yield from self.parse_section(subsection)
        snipped_selector = section.xpath(PATTERN.CHILD_CODE_SNIPPETS)
        code_snippets = list(map(parse_highlighted_code, snipped_selector))
        yield {
            "url": section_url,
            "code_snippets": code_snippets
        }

