import os.path
import ast
import ast_parser
import itertools
import pygments
from pygments.lexers import Python3Lexer
from pygments.formatters import HtmlFormatter
from whoosh.index import exists_in, create_in, open_dir
from whoosh.fields import Schema, TEXT, ID
from whoosh.query import Term


def create_new_index(path, name, tokenizer_options):
    if exists_in(path, name):
        raise RuntimeError("Index already exists at {}".format(path))
    schema = Schema(
        title=TEXT(stored=True),
        url=ID(stored=True, unique=True),
        content=TEXT(stored=True, analyzer=ast_parser.ASTTokenizer(**tokenizer_options))
    )
    os.mkdir(path)
    return create_in(path, schema, indexname=name)


def all_linenumbers(root):
    return [node.lineno for node in ast.walk(root) if hasattr(node, "lineno")]

def subsequence_increasing_by_one(seq):
    return ([seq[0]] +
            [x for _, x in
             itertools.takewhile(
                 lambda t: abs(t[0] - t[1]) == 1,
                 zip(seq, seq[1:]))])


#TODO incremental indexing and housekeeping
class Index:
    def __init__(self, index_path, name, tokenizer_options):
        if not exists_in(index_path, name):
            raise RuntimeError("There is no index at {}".format(index_path))
        self.index = open_dir(index_path, name)
        self.name = name
        self.tokenizer_options = tokenizer_options

    def valid_content(self, content):
        try:
            ast.parse(content)
        except SyntaxError:
            return False
        return True

    def add_document(self, data):
        if not self.valid_content(data['content']):
            return False
        writer = self.index.writer()
        writer.add_document(title=data['title'], url=data['url'], content=data['content'])
        writer.commit()
        return True

    def add_documents(self, data):
        writer = self.index.writer()
        for code in data['code_snippets']:
            if not self.valid_content(code):
                continue
            writer.add_document(title=data['title'], url=data['url'], content=code)
        writer.commit()

    def update_documents(self, data):
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
        for hit in self.get_documents(code):
            data = {'title': hit['title'], 'url': hit['url']}
            matched_tokens = set(pair[1] for pair in hit.matched_terms() if pair[0] == 'content')
            data['matched_tokens_count'] = len(matched_tokens)
            data['source_html_highlighted'], highlighted_lines = self.highlight_matches(hit['content'], matched_tokens)
            first_highlighted_range = subsequence_increasing_by_one(highlighted_lines)
            if len(first_highlighted_range) == 1:
                data['url'] += "#L{}".format(first_highlighted_range[0])
            else:
                data['url'] += "#L{}-L{}".format(first_highlighted_range[0], first_highlighted_range[-1])
            yield data


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

