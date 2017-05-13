import os.path
import shutil
from whoosh.index import create_in
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import QueryParser
from ast_parser import ASTTokenizer


def create_new_index(path, force=False):
    schema = Schema(
        title=TEXT(stored=True),
        url=ID(stored=True),
        content=TEXT(analyzer=ASTTokenizer(tokenize_leaves=False))
    )
    if os.path.exists(path):
        if force:
            shutil.rmtree(path)
        else:
            raise RuntimeError("Index at {} already exists, not removing without force flag set to True.".format(path))
    os.mkdir(path)
    return create_in(path, schema)


class Index:
    def __init__(self, index_path, name):
        self.index = create_new_index(index_path)
        self.name = name

    def add_documents(self, docs):
        writer = self.index.writer()
        for doc in docs:
            writer.add_document(**doc)
        writer.commit()

    def get_documents(self, query_string):
        query_parser = QueryParser("content", self.index.schema)
        query = query_parser.parse(query_string)
        with self.index.searcher() as searcher:
            for result in searcher.search(query):
                yield result

