import flask
import json
import pygments
from pygments.lexers import Python3Lexer
from pygments.formatters import HtmlFormatter
from ..parsers import ast_parser

flask_app = flask.Flask(__name__)

@flask_app.route("/")
def index():
    return flask.render_template('index.html')

@flask_app.route("/parse", methods=("POST", ))
def parse():
    render_context = dict()
    try:
        # Parse spaghetti
        raw_text = flask.request.form['spaghetti']
        # TODO: paging
        similar_snippets = get_similar_snippets(raw_text)
        render_context["similar"] = similar_snippets
    except SyntaxError as syntax_error:
        render_context["errors"] = str(syntax_error)
    return flask.render_template('parsed.html', **render_context)

# TEMP, should be from DB
def all_snippets():
    with open("out.json") as f:
        snippets = json.load(f)
    for page in snippets:
        if not page["code_snippets"]:
            continue
        yield page


def html_highlight(code, line_numbers):
    format_options = {
        "hl_lines": line_numbers,
    }
    return pygments.highlight(
        code,
        Python3Lexer(),
        HtmlFormatter(**format_options)
    )


def get_similar_snippets(code):
    similar = list()
    total_snippets_count = 0
    for result in all_snippets(): # snippet is actually iterable of snippets
        for snippet in result["code_snippets"]:
            total_snippets_count += 1
            line_numbers = ast_parser.get_similar_lines(code, snippet, 2)
            if not line_numbers:
                continue
            print("{} lines in common for:".format(len(line_numbers)))
            print("-"*30)
            print(code)
            print("-"*30)
            print(snippet)
            print("-"*30)
            print("numbers:")
            for t in line_numbers:
                print(t)
            print()
            similar.append({
                "section_title": result["title"],
                "url": result["url"],
                "source": html_highlight(snippet, [t[1] for t in line_numbers]),
                "similar_lines": len(line_numbers)
            })
    similar.sort(key=lambda d: d["similar_lines"], reverse=True)
    print("compared {} snippets".format(total_snippets_count))
    print("returning {} similar similar_snippets".format(len(similar)))
    return similar

if __name__ == "__main__":
    flask_app.run()

