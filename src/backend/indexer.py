import os.path
import ast
import ast_parser
import result_formatter
import itertools
from whoosh.index import exists_in, create_in, open_dir
from whoosh.fields import Schema, TEXT, ID
from whoosh.query import Term, Every


def create_new_index(path, name, tokenizer_options):
    if exists_in(path, name):
        raise RuntimeError("Index already exists at {}".format(path))
    schema = Schema(
        title=TEXT(stored=True),
        url=ID(stored=True, unique=True),
        content=TEXT(stored=True, analyzer=ast_parser.ASTTokenizer(tokenizer_options))
    )
    os.mkdir(path)
    return create_in(path, schema, indexname=name)


def all_linenumbers(root):
    return [node.lineno for node in ast.walk(root) if hasattr(node, "lineno")]


def subsequence_increasing_by_one(seq):
    """
    Take elements from seq while their values are increasing and their difference is one.
    For example: seq = (5, 6, 7, 12, 13, ...) returns [5, 6, 7]
    """
    return ([seq[0]] +
            [x for _, x in
             itertools.takewhile(
                 lambda t: abs(t[0] - t[1]) == 1,
                 zip(seq, seq[1:]))])


def LIS_by_one_starting_index(seq):
    """
    Return the index in a sorted seq at which the longest increasing subsequence, that increases by a difference of one, starts.
    For example: seq = (1, 5, 6, 9, 10, 11, 12, 39, 40)
    returns 3 because 9, 10, 12 starts at 3
    """
    assert seq
    index = candidate_index = increasing_count = max_increasing_count = 0
    increasing = True
    for i in range(1, len(seq)):
        if seq[i] - seq[i-1] == 1:
            if not increasing:
                increasing = True
                candidate_index = i-1
            increasing_count += 1
            if increasing_count > max_increasing_count:
                max_increasing_count = increasing_count
                index = candidate_index
        elif increasing:
            increasing_count = 0
            increasing = False
    return index


def content_is_valid_code(content):
    try:
        ast.parse(content)
    except SyntaxError:
        return False
    return True


#TODO incremental indexing and housekeeping
class Index:
    def __init__(self, index_path, name, tokenizer_options):
        if not exists_in(index_path, name):
            raise RuntimeError("There is no index at {}".format(index_path))
        self.index = open_dir(index_path, name)
        self.name = name
        self.tokenizer_options = tokenizer_options

    def add_document(self, data):
        if not content_is_valid_code(data['content']):
            return False
        writer = self.index.writer()
        writer.add_document(title=data['title'], url=data['url'], content=data['content'])
        writer.commit()
        return True

    def add_documents(self, data):
        writer = self.index.writer()
        for code in data['code_snippets']:
            if not content_is_valid_code(code):
                continue
            writer.add_document(title=data['title'], url=data['url'], content=code)
        writer.commit()

    def update_documents(self, data):
        writer = self.index.writer()
        for code in data['code_snippets']:
            writer.update_document(title=data['title'], url=data['url'], content=code)
        writer.commit()

    def iter_documents(self):
        with self.index.searcher() as searcher:
            for result in searcher.search(Every()):
                yield result

    def __len__(self):
        with self.index.searcher() as searcher:
            return searcher.doc_count()

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
            is_python_docs = "docs.python.org" in hit['url']
            if is_python_docs:
                repo, filename = "Python Docs", hit['title']
            else:
                repo, filename = tuple(hit['title'].split(" "))
            data = {'title': {'repo': repo, 'filename': filename},
                    'url': hit['url']}
            matched_tokens = set(pair[1]
                                 for pair in hit.matched_terms()
                                 if pair[0] == 'content')
            data['matched_tokens_count'] = len(matched_tokens)
            data['source_html_highlighted'], highlighted_lines = self.highlight_matches(hit['content'], matched_tokens)
            if not is_python_docs:
                first_highlighted_range = subsequence_increasing_by_one(highlighted_lines)
                if len(first_highlighted_range) == 1:
                    data['url'] += "#L{}".format(first_highlighted_range[0])
                else:
                    data['url'] += "#L{}-L{}".format(first_highlighted_range[0], first_highlighted_range[-1])
            yield data


    # TODO: implement a custom lexer to highlight matching tokens instead of the whole line containing a matching token
    # TODO: make the use the line_numbers more consistent
    def highlight_matches(self, code, matched_tokens):
        line_numbers = set()
        # TODO: when found a matching subtree, don't traverse its children
        for node in ast.walk(ast.parse(code)):
            dumps = ast_parser.dump(node, **self.tokenizer_options)
            node_dump = next(dumps, '').encode()
            if node_dump in matched_tokens:
                line_numbers |= set(all_linenumbers(node))
        # Drop scattered matches from the beginning if there is a
        # larger chunk match in the middle
        line_numbers = sorted(line_numbers)
        line_numbers = line_numbers[LIS_by_one_starting_index(line_numbers):]
        return result_formatter.html_highlight(code, line_numbers), line_numbers


