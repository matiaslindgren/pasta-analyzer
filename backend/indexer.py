import os.path
import ast
import ast_parser
from whoosh.index import create_in
from whoosh.fields import Schema, TEXT, ID
from whoosh.query import Term


def create_new_index(path, **tokenizer_options):
    schema = Schema(
        title=TEXT(stored=True),
        url=ID(stored=True),
        content=TEXT(analyzer=ast_parser.ASTTokenizer(**tokenizer_options))
    )
    if os.path.exists(path):
        raise RuntimeError("Index at {} already exists.".format(path))
    os.mkdir(path)
    return create_in(path, schema)


class Index:
    def __init__(self, index_path, name, **tokenizer_options):
        self.index = create_new_index(index_path, **tokenizer_options)
        self.name = name
        self.tokenizer_options = tokenizer_options

    def add_document(self, data):
        writer = self.index.writer()
        for code in data['code_snippets']:
            writer.add_document(title=data['title'], url=data['url'], content=code)
        writer.commit()

    def parse_query(self, code_query):
        subtrees = ast_parser.dump(ast.parse(code_query), **self.tokenizer_options)
        full_tree = next(subtrees)
        query = Term(u"content", full_tree)
        for subtree in subtrees:
            query |= Term(u"content", subtree)
        return query

    def get_documents(self, code_query):
        with self.index.searcher() as searcher:
            for result in searcher.search(self.parse_query(code_query)):
                yield result

