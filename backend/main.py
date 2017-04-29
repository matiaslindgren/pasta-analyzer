import flask
import ast
import collections

flask_app = flask.Flask(__name__)

def count_syntax(source_string):
    c = collections.Counter()
    class NodeVisitor(ast.NodeVisitor):
        def generic_visit(self, node):
            c[node.__class__.__name__.split(".")[-1]] += 1
            super().generic_visit(node)
    NodeVisitor().visit(ast.parse(source_string))
    return c

@flask_app.route("/")
def index():
    return flask.render_template('index.html')

@flask_app.route("/parse", methods=("POST", ))
def parse():
    render_context = dict()
    try:
        given_spaghetti = flask.request.form['spaghetti']
        render_context["parsed_spaghetti"] = count_syntax(given_spaghetti).items()
    except SyntaxError as syntax_error:
        render_context["errors"] = str(syntax_error)
    return flask.render_template('parsed.html', **render_context)

if __name__ == "__main__":
    flask_app.run()

