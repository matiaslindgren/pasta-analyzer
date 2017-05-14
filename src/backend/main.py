import flask
import init_apps
import argparse


flask_app = init_apps.make_flask(__name__)
index = init_apps.make_index(__name__)


@flask_app.route("/")
def root():
    return flask.render_template('index.html')


@flask_app.route("/parse", methods=("POST", ))
def parse():
    render_context = dict()
    try:
        raw_text = flask.request.form['spaghetti']
        similar_snippets = index.get_similar_snippets(raw_text)
        render_context["similar"] = similar_snippets
    except SyntaxError as syntax_error:
        render_context["errors"] = str(syntax_error)
    return flask.render_template('parsed.html', **render_context)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--build_index")
    args = parser.parse_args()

    if args.build_index:
        print("Indexing")
        import json
        with open("data.json") as f:
            for d in json.load(f):
                index.add_document(d)
        print("Indexing finished")

    flask_app.run()


