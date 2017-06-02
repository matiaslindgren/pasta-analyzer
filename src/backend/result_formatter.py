import settings
import pygments
from pygments.lexers import Python3Lexer
from pygments.formatters import HtmlFormatter


def html_highlight(code, line_numbers):
    format_options = {
        "hl_lines": sorted(line_numbers),
        "linenos": "table"
    }
    lexer = Python3Lexer()
    format_options["hl_lines"] = [n - min(line_numbers) + 2  for n in line_numbers]
    lexer.add_filter(LineFilter(line_numbers, settings.MAX_LINES_IN_SEARCH_RESULT_CODE_BLOCK))
    # print("highlighting {}".format(" ".join(map(str, format_options["hl_lines"]))))
    format_options["linenostart"] = max(1, min(line_numbers)-1)
    return pygments.highlight(
        code,
        lexer,
        HtmlFormatter(**format_options))


class LineFilter(pygments.filter.Filter):
    def __init__(self, line_numbers, max_lines, **options):
        super().__init__(**options)
        smallest = min(line_numbers)
        self.include_lines = line_numbers | set(i for i in range(smallest, max(1, smallest-3), -1))
        self.max_lines = max_lines
        # print("include lines {}".format(" ".join(map(str, self.include_lines))))

    def filter(self, lexer, stream):
        current_lineno = 1
        yielding = False
        yielded = 0
        for token, value in stream:
            # print((token, value, current_lineno, yielded, yielding))
            if yielded > self.max_lines:
                return
            newline_count = value.count("\n")
            if yielding:
                yield token, value
                yielded += newline_count
            elif any(lineno in self.include_lines
                     for lineno in
                     range(current_lineno, current_lineno+newline_count)):
                yielding = True
            current_lineno += newline_count

