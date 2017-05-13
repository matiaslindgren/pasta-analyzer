import flask
import json
import pygments
from pygments.lexers import Python3Lexer
from pygments.formatters import HtmlFormatter
from ..parsers import ast_parser

flask_app = flask.Flask(__name__)
index = indexing.Index("index", __name__)

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

def get_similar_snippets(string):


# TEMP, should be from DB
def all_snippets():
    snippets = list()
    for i in range(1, 3):
        with open("out{}.json".format(i)) as f:
            snippets.extend(json.load(f))
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
            _, snippet_linenos_similar = ast_parser.get_similar_lines(code, snippet, 1)
            if not snippet_linenos_similar:
                continue
            similar.append({
                "section_title": result["title"],
                "url": result["url"],
                "source": html_highlight(snippet, list(snippet_linenos_similar)),
                "similar_lines": len(snippet_linenos_similar)
            })
    similar.sort(key=lambda d: d["similar_lines"], reverse=True)
    print("compared {} snippets".format(total_snippets_count))
    print("returning {} similar similar_snippets".format(len(similar)))
    return similar

if __name__ == "__main__":
    flask_app.run()

