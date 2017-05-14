import flask
import settings
import indexer

def make_flask(name):
    return flask.Flask(name)

def load_index():
    return indexer.Index(
        settings.INDEX_DIRNAME,
        settings.INDEX_NAME,
        settings.TOKENIZER_OPTIONS
    )


