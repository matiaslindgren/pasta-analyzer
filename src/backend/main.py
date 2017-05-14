import flask
import ast
import ast_parser
import pygments
from pygments.lexers import Python3Lexer
from pygments.formatters import HtmlFormatter
import indexer

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
        similar_snippets = index.get_similar_snippets(raw_text)
        render_context["similar"] = similar_snippets
    except SyntaxError as syntax_error:
        render_context["errors"] = str(syntax_error)
    return flask.render_template('parsed.html', **render_context)


if __name__ == "__main__":

    # print("Indexing")
    # import json
    # with open("data.json") as f:
    #     for d in json.load(f):
    #         index.add_document(d)
    # print("Indexing finished")

    flask_app.run()


