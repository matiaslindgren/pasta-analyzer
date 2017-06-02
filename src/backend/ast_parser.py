import ast
import itertools
from whoosh.analysis import Tokenizer
from whoosh.analysis.acore import Token


def preorder(node, depth=0):
    yield node, depth
    for child in ast.iter_child_nodes(node):
        yield from preorder(child, depth+1)


def has_depth_at_least(root, min_depth):
    return any(depth >= min_depth for _, depth in preorder(root))


def name_dump(root):
    return ' '.join(node.__class__.__name__ for node, _ in preorder(root))


class ASTTokenizer(Tokenizer):
    def __init__(self, **dump_options):
        self.dump_options = dump_options

    def __call__(self, source_string, positions=False, chars=False,
                 keeporiginal=False, start_pos=0, removestops=False,
                 start_char=0, tokenize=True, mode='', **kwargs):
        t = Token(positions, chars, removestops=removestops, mode=mode)
        all_subtrees = dump(ast.parse(source_string), **self.dump_options)
        full_tree = next(all_subtrees)
        for pos, subtree in enumerate(itertools.chain((full_tree, ), all_subtrees)):
            t.text = subtree
            t.boost = 1.0
            if keeporiginal:
                t.original = t.text
            t.stopped = False
            if positions:
                t.pos = start_pos + pos
            if chars:
                t.startchar = start_char + full_tree.index(subtree)
                t.endchar = start_char + t.startchar + len(subtree)
            yield t


def dump(node, annotate_fields=True, include_attributes=False,
         drop_field_names=None, drop_field_values=None, min_depth=None,
         max_depth=None):
    """
    Adapted from ast.dump, original: https://github.com/python/cpython/blob/master/Lib/ast.py#L88
    """
    if min_depth and max_depth:
        assert min_depth < max_depth
    if drop_field_names is None:
        drop_field_names = set()
    if drop_field_values is None:
        drop_field_values = set()
    def name(node):
        return node.__class__.__name__
    def _format(node, depth):
        if max_depth is not None and depth > max_depth:
            return name(node)
        elif isinstance(node, ast.AST):
            fields = [(a, _format(b, depth+1))
                      for a, b in ast.iter_fields(node)]
            rv = '%s(%s' % (name(node), ', '.join(
                ('%s=%s' % field
                 for field in fields
                 if field[0] not in drop_field_names and
                    field[1] not in drop_field_values)
                if annotate_fields else
                (b for a, b in fields)
            ))
            if include_attributes and node._attributes:
                rv += fields and ', ' or ' '
                rv += ', '.join('%s=%s' % (a, _format(getattr(node, a), depth+1))
                                for a in node._attributes)
            return rv + ')'
        elif isinstance(node, list):
            if not node:
                return '[]'
            return '[%s]' % ', '.join(_format(n, depth+1) for n in node)
        return repr(node)
    if not isinstance(node, ast.AST):
        raise TypeError('expected AST, got %r' % name(node))
    for subtree, _ in preorder(node):
        if min_depth is not None and not has_depth_at_least(subtree, min_depth):
            continue
        yield _format(subtree, 0)


