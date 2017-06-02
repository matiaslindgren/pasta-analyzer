import flask
import init_apps
import argparse


flask_app = init_apps.make_flask(__name__)
index = init_apps.load_index()


@flask_app.route("/")
def root():
    return flask.render_template('index.html')


@flask_app.route("/parse")
def parse():
    render_context = dict()
    try:
        raw_text = flask.request.args.get('spaghetti')
        print(raw_text)
        similar_snippets = list(index.get_similar_snippets(raw_text))
        render_context["similar"] = similar_snippets
    except SyntaxError as syntax_error:
        render_context["errors"] = str(syntax_error)
    if flask.request.args.get("hasJavascript"):
        print("has javascript")
        return json.dumps(render_context)
    print("no javascript")
    return flask.render_template('parsed.html', **render_context)


if __name__ == "__main__":
    flask_app.run()


