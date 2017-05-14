import os.path
import ast
import ast_parser
import pygments
from pygments.lexers import Python3Lexer
from pygments.formatters import HtmlFormatter
from whoosh.index import exists_in, create_in, open_dir
from whoosh.fields import Schema, TEXT, ID
from whoosh.query import Term


def create_new_index(path, name, tokenizer_options):
    schema = Schema(
        title=TEXT(stored=True),
        url=ID(stored=True, unique=True),
        content=TEXT(stored=True, analyzer=ast_parser.ASTTokenizer(**tokenizer_options))
    )
    if os.path.exists(path):
        raise RuntimeError("Index at {} already exists.".format(path))
    os.mkdir(path)
    return create_in(path, schema, indexname=name)


def all_linenumbers(root):
    return [node.lineno for node in ast.walk(root) if hasattr(node, "lineno")]



#TODO incremental indexing and housekeeping
class Index:
    def __init__(self, index_path, name, tokenizer_options):
        if exists_in(index_path, name):
            self.index = open_dir(index_path, name)
        else:
            self.index = create_new_index(index_path, name, tokenizer_options)
        self.name = name
        self.tokenizer_options = tokenizer_options

    def add_document(self, data):
        writer = self.index.writer()
        for code in data['code_snippets']:
            writer.add_document(title=data['title'], url=data['url'], content=code)
        writer.commit()

    def update_document(self, data):
        writer = self.index.writer()
        for code in data['code_snippets']:
            writer.update_document(title=data['title'], url=data['url'], content=code)
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
            for result in searcher.search(self.parse_query(code_query), terms=True):
                yield result

    def get_similar_snippets(self, code):
        similar = []
        for hit in self.get_documents(code):
            data = {'title': hit['title'], 'url': hit['url'], 'matched': hit.matched_terms()}
            matched_tokens = set(pair[1] for pair in hit.matched_terms() if pair[0] == 'content')
            data['content'] = self.highlight_matches(hit['content'], matched_tokens)
            similar.append(data)
        return similar


    # TODO: implement a custom lexer to highlight matching tokens instead of the whole line containing a matching token
    def highlight_matches(self, code, matched_tokens):
        line_numbers = list()
        for node in ast.walk(ast.parse(code)):
            dumps = ast_parser.dump(node, **self.tokenizer_options)
            node_dump = next(dumps, '').encode()
            if node_dump in matched_tokens:
                line_numbers.extend(all_linenumbers(node))
        return self.html_highlight(code, line_numbers)


    def html_highlight(self, code, line_numbers):
        format_options = {
            "hl_lines": line_numbers,
        }
        return pygments.highlight(
            code,
            Python3Lexer(),
            HtmlFormatter(**format_options)
        )

