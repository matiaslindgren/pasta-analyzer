import flask
import init_apps
import json


flask_app = init_apps.make_flask(__name__)
index = init_apps.load_index()


@flask_app.route("/")
def root():
    return flask.render_template("index.html", is_index_page=True)


@flask_app.route("/parse")
def parse():
    render_context = dict()
    try:
        raw_text = flask.request.args.get("spaghetti").lstrip()
        render_context["previous_input"] = raw_text
        similar_snippets = list(index.get_similar_snippets(raw_text))
        render_context["similar"] = similar_snippets
        render_context["has_results"] = len(similar_snippets) > 0
    except SyntaxError as syntax_error:
        render_context["errors"] = str(syntax_error)
    if flask.request.args.get("hasJavascript"):
        return json.dumps(render_context)
    return flask.render_template("index.html", **render_context)


# TODO: add LRU caching
@flask_app.route("/about")
def about():
    with flask_app.open_resource("cloned_meta.json", "r") as f:
        render_context = json.load(f)
    render_context["documents"] = len(index)
    return flask.render_template("about.html", **render_context)


if __name__ == "__main__":
    flask_app.run()


