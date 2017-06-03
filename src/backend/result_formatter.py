import settings
import pygments
from pygments.lexers import Python3Lexer
from pygments.formatters import HtmlFormatter


def html_highlight(code, line_numbers):
    format_options = {
        "hl_lines": line_numbers,
        "linenos": "table"
    }
    print("generating html with highlighted {}".format(" ".join(map(str, line_numbers))))
    lexer = Python3Lexer()
    max_lines = settings.MAX_LINES_IN_SEARCH_RESULT_CODE_BLOCK
    lexer.add_filter(LineFilter(line_numbers, max_lines))
    format_options["hl_lines"] = [n - min(line_numbers) + 1  for n in line_numbers]
    format_options["linenostart"] = max(1, min(line_numbers) - 1)
    print("hl_lines {}".format(" ".join(map(str, format_options['hl_lines']))))
    print("linenostart {}".format(format_options['linenostart']))
    print("code")
    for i, line in enumerate(code.splitlines(), start=1):
        print("{}{} {}".format(">>" if i in line_numbers else "", i, line))
    return pygments.highlight(
        code,
        lexer,
        HtmlFormatter(**format_options))


class LineFilter(pygments.filter.Filter):
    def __init__(self, line_numbers, max_lines, **options):
        super().__init__(**options)
        # smallest = min(line_numbers)
        self.include_lines = set(line_numbers)
        print("linefilter with include lines {}".format(" ".join(map(str, self.include_lines))))
        # | set(i for i in range(smallest, max(1, smallest-3), -1))
        self.max_lines = max_lines

    def filter(self, lexer, stream):
        current_lineno = 1
        yielding = False
        yielded = 0
        for token, value in stream:
            # print((current_lineno, yielding, yielded, token, value))
            if yielded > self.max_lines:
                print("yielded max lines, stopping")
                return
            newline_count = value.count("\n")
            if not yielding and current_lineno in self.include_lines:
                print("start yielding at lineno {}".format(current_lineno))
                yielding = True
            if yielding:
                yield token, value
                yielded += newline_count
            current_lineno += newline_count

