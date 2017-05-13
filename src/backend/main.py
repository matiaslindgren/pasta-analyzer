import flask
import json
import pygments
import indexer
import ast_parser
from pygments.lexers import Python3Lexer
from pygments.formatters import HtmlFormatter

flask_app = flask.Flask(__name__)
index = indexer.Index("index", __name__)

@flask_app.route("/")
def root():
    return flask.render_template('index.html')

@flask_app.route("/parse", methods=("POST", ))
def parse():
    render_context = dict()
    try:
        # Parse spaghetti
        raw_text = flask.request.form['spaghetti']
        similar_snippets = get_similar_snippets(raw_text)
        print("{} similar snippets".format(len(similar_snippets)))
        render_context["similar"] = similar_snippets
    except SyntaxError as syntax_error:
        render_context["errors"] = str(syntax_error)
    return flask.render_template('parsed.html', **render_context)


def get_similar_snippets(code):
    return [{'url': data['url'], 'title': data['title']} for data in index.get_documents(code)]


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



if __name__ == "__main__":

    # print("Indexing")
    # import json
    # with open("data.json") as f:
    #     for d in json.load(f):
    #         index.add_document(d)
    # print("Indexing finished")

    flask_app.run()


