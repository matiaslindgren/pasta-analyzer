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
        similar_snippets = get_similar_snippets(raw_text)
        print("{} similar snippets".format(len(similar_snippets)))
        render_context["similar"] = similar_snippets
    except SyntaxError as syntax_error:
        render_context["errors"] = str(syntax_error)
    return flask.render_template('parsed.html', **render_context)


def get_similar_snippets(code):
    similar = []
    for hit in index.get_documents(code):
        data = {'title': hit['title'], 'url': hit['url'], 'matched': hit.matched_terms()}
        matched_tokens = set(pair[1] for pair in hit.matched_terms() if pair[0] == 'content')
        data['content'] = highlight_matches(hit['content'], matched_tokens)
        similar.append(data)
    return similar


def all_linenumbers(root):
    return [node.lineno for node in ast.walk(root) if hasattr(node, "lineno")]


# TODO: implement a custom lexer to highlight matching tokens instead of the whole line containing a matching token
def highlight_matches(code, matched_tokens):
    line_numbers = list()
    for node in ast.walk(ast.parse(code)):
        dumps = ast_parser.dump(node, tokenize_leaves=False)
        node_dump = next(dumps, '').encode()
        if node_dump in matched_tokens:
            line_numbers.extend(all_linenumbers(node))
    return html_highlight(code, line_numbers)

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


