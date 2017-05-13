import indexer, tempfile, ast
import ast_parser
from whoosh.query import Term


with tempfile.TemporaryDirectory() as td:
    print("create index")
    i = indexer.Index(td + "index", "asd")
    w = i.index.writer()
    print("add document")
    w.add_document(title=u"hello", url=u"code.com", content=u"def f(x):\n return x - 2")
    w.commit()
    print("committed")
    print("parse query")
    for query_code in (
            u"class A:\n def __init__(self):\n  pass",
            u"a + 2 - 3",
            u"def function(x):\n pass",
            u"def function(x, y):\n return x - 2",
            u"class A(x, y):\n def __init__(self, x):\n  x += 1\n  return list.sort",
            ):
        subtrees = ast_parser.dump(ast.parse(query_code), tokenize_leaves=False)
        q = Term(u"content",  next(subtrees))
        for st in subtrees:
            q |= Term(u"content", st)
        with i.index.searcher() as searcher:
            for result in searcher.search(q):
                print(result)
