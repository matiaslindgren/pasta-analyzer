import flask
import ast
import collections

flask_app = flask.Flask(__name__)

def count_syntax(source_string):
    #TODO: extract and chop at least Call and Load nodes
    #NOTE, this is not trivial, some sensible consistency must be invented before implementing this any further
    counted_nodes = collections.Counter()
    class NodeVisitor(ast.NodeVisitor):
        def generic_visit(self, node):
            node_name = node.__class__.__name__
            if node_name == "Call" and hasattr(node, 'func') and hasattr(node.func, 'id'):
                counted_nodes["Function:" + node.func.id] += 1
                # else:
                    # raise RuntimeError("Found a Call node without 'func' attribute, Call node has fields {}".format(list(ast.iter_fields(node))))
            else:
                counted_nodes[node_name] += 1
            super().generic_visit(node)
    NodeVisitor().visit(ast.parse(source_string))
    return counted_nodes

@flask_app.route("/")
def index():
    return flask.render_template('index.html')

@flask_app.route("/parse", methods=("POST", ))
def parse():
    render_context = dict()
    try:
        # Parse spaghetti
        raw_text = flask.request.form['spaghetti']
        name_count = count_syntax(raw_text)
        sorted_name_counts = ((key, name_count[key]) for key in sorted(name_count.keys()))
        render_context["parsed_spaghetti"] = sorted_name_counts
    except SyntaxError as syntax_error:
        render_context["errors"] = str(syntax_error)
    return flask.render_template('parsed.html', **render_context)

if __name__ == "__main__":
    flask_app.run()

