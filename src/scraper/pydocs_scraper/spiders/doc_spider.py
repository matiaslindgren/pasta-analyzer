"""
Scrapy spiders for crawling the Python docs.
"""
import scrapy
import re
import urllib
import ast


class PATTERN:
    """
    XPath selectors and other string constants.
    """
    _SECTION_DIV         = "div[contains(@class, 'section')]"
    ALL_PAGE_SECTIONS    = ".//" + _SECTION_DIV
    CHILD_PAGE_SECTIONS  = "./" + _SECTION_DIV
    LIST_PAGE_SECTIONS   = "./{}/dl".format(_SECTION_DIV)
    TOCTREE_TOP_LINKS    = "//ul/li[contains(@class, 'toctree-l1')]/a"
    SECTION_HEADER_TEXT  = "|".join("((./h{0}/text())|(./h{0}//code//text()))".format(i) for i in range(1, 4))
    DEFINITIONS          = "./dl"
    CHILD_DEFINITIONS    = "./dd/dl"
    DEFINITION_NAME      = "./dt/@id"
    DEFINITION_LINKS     = "./dt/a[contains(@class, 'headerlink')]/@href"
    HEADER_SECTION_LINKS = "|".join("(.//h{}/a[contains(@class, 'headerlink')]/@href)".format(i) for i in range(1, 4))
    INTERNAL_LINKS       = ".//dd//a[contains(@class, 'internal reference') or contains(@class, 'reference internal')]/@href"
    CHILD_CODE_SNIPPETS  = "./div[contains(@class, 'highlight-python3')]"
    DEFINITION_CODE_SNIPPETS  = "./dd/div[contains(@class, 'highlight-python3')]"
    HREF                 = ".//@href"
    ALL_TEXT             = ".//text()"
    SHELL_STRINGS        = (
        ">>>",
        "...",
    )


def is_valid_code(code):
    if not isinstance(code, str):
        return False
    try:
        ast.parse(code)
    except SyntaxError:
        return False
    return True


def amount_of_nodes(code):
    if not is_valid_code(code):
        return 0
    return len(list(ast.walk(ast.parse(code))))


def parse_highlighted_code(snippet_selector):
    """
    Return the html highlighted code selected by the scrapy.Selector given as parameter as a plain string without shell characters.
    """
    def no_shell_characters_in(string):
        shell_pattern = re.compile("|".join("^" + re.escape(p) for p in PATTERN.SHELL_STRINGS))
        return re.search(shell_pattern, string) is None
    unhighlighted_code_pieces = snippet_selector.xpath(PATTERN.ALL_TEXT).extract()
    return ''.join(filter(no_shell_characters_in, unhighlighted_code_pieces))


def get_section_url(s):
    return s.xpath(PATTERN.HEADER_SECTION_LINKS).extract_first()


def get_section_title(s):
    return ''.join(s.xpath(PATTERN.SECTION_HEADER_TEXT).extract())


def get_definition_title(dl):
    return dl.xpath(PATTERN.DEFINITION_NAME).extract_first()


def get_definition_url(dl):
    return dl.xpath(PATTERN.DEFINITION_LINKS).extract_first()


# TODO we must go deeper, currently indexing only top level
# http://localhost:8000/library/stdtypes.html#memoryview
# http://localhost:8000/library/stdtypes.html#memoryview.__eq__
class LibrarySpider(scrapy.Spider):
    name = "library"
    start_urls = (
        # 'http://docs.python.org/3/library',
        'http://localhost:8000/library',
    )

    def parse(self, response):
        self.logger.debug("Parsing response {}".format(response))
        toctree_links = response.xpath(PATTERN.TOCTREE_TOP_LINKS)
        if not toctree_links:
            yield from self.parse_page(response)
        else:
            for page in toctree_links:
                next_url = response.urljoin(page.xpath(PATTERN.HREF).extract_first())
                yield scrapy.Request(next_url, self.parse)

    def parse_page(self, page):
        """
        Helper method for starting the parse of all sections on 'page' from the root section.
        """
        self.logger.debug("Parsing page {}".format(page))
        sections = page.xpath(PATTERN.ALL_PAGE_SECTIONS)
        if not sections:
            self.logger.warning("Page has no parsable sections")
            return None
        yield from self.parse_section(sections[0], page)

    def parse_section(self, section, page):
        """
        Recursively yield dicts of url string and code snippets list within 'section' and all its nested sections.
        The data within a nested section is not included into the data of its parent, unless it is explicitly duplicate in the html.
        """
        section_url = page.urljoin(get_section_url(section))
        self.logger.debug("Parsing section {}".format(section_url))
        for subsection in section.xpath(PATTERN.CHILD_PAGE_SECTIONS):
            yield from self.parse_section(subsection, page)
        for dl in section.xpath(PATTERN.DEFINITIONS):
            yield from self.parse_definition_description(dl, section, section_url)
        snippet_selector = section.xpath(PATTERN.CHILD_CODE_SNIPPETS)
        if not snippet_selector:
            return
        code_snippets = map(parse_highlighted_code, snippet_selector)
        valid_code = list()
        skipped_count = 0
        for snippet in code_snippets:
            if is_valid_code(snippet) and amount_of_nodes(snippet) > 1:
                valid_code.append(snippet)
            else:
                skipped_count += 1
        if skipped_count > 0:
            self.logger.debug("Found {} snippets with invalid Python syntax and they were skipped".format(skipped_count))
        yield {
            "title": get_section_title(section),
            "url": page.urljoin(section_url),
            "code_snippets": valid_code
        }

    def parse_definition_description(self, definition, parent, parent_url):
        for child_definition in definition.xpath(PATTERN.CHILD_DEFINITIONS):
            yield from self.parse_definition_description(child_definition, definition, parent_url)
        snippet_selector = definition.xpath(PATTERN.DEFINITION_CODE_SNIPPETS)
        if not snippet_selector:
            return
        code_snippets = map(parse_highlighted_code, snippet_selector)
        valid_code = list()
        skipped_count = 0
        for snippet in code_snippets:
            if is_valid_code(snippet) and amount_of_nodes(snippet) > 1:
                valid_code.append(snippet)
            else:
                skipped_count += 1
        if skipped_count > 0:
            self.logger.debug("Found {} snippets with invalid Python syntax and they were skipped".format(skipped_count))
        yield {
            "title": "{}: {}".format(
                get_section_title(parent),
                get_definition_title(definition)),
            "url": urllib.parse.urljoin(parent_url, get_definition_url(definition)),
            "code_snippets": valid_code
        }


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
        # As of May 2017, every section (1. Introduction, 2. ...)
        # in the Python docs have their own html document with only
        # one root level section, with all subsections nested within
        yield from self.parse_section(sections[0], page)

    def parse_section(self, section, page):
        """
        Recursively yield dicts of url string and code snippets list within 'section' and all its nested sections.
        The data within a nested section is not included into the data of its parent, unless it is explicitly duplicate in the html.
        """
        section_url = get_section_url(section)
        self.logger.debug("Parsing section {}".format(section_url))
        for subsection in section.xpath(PATTERN.CHILD_PAGE_SECTIONS):
            yield from self.parse_section(subsection, page)
        snippet_selector = section.xpath(PATTERN.CHILD_CODE_SNIPPETS)
        if not snippet_selector:
            return
        code_snippets = map(parse_highlighted_code, snippet_selector)
        valid_code = list()
        skipped_count = 0
        for snippet in code_snippets:
            if is_valid_code(snippet) and amount_of_nodes(snippet) > 1:
                valid_code.append(snippet)
            else:
                skipped_count += 1
        if skipped_count > 0:
            self.logger.debug("Found {} snippets with invalid Python syntax and they were skipped".format(skipped_count))
        yield {
            "title": get_section_title(section),
            "url": page.urljoin(section_url),
            "code_snippets": valid_code
        }

