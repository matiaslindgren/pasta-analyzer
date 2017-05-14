import flask
import settings
import indexer

def make_flask(name):
    return flask.Flask(name)

def make_index(name):
    return indexer.Index(
        settings.INDEX_DIRNAME,
        name,
        settings.TOKENIZER_OPTIONS
    )


