import ast


def is_python_source(code):
    if not isinstance(code, str):
        return False
    try:
        ast.parse(code)
    except SyntaxError:
        return False
    return True


def preorder(node, h=0):
    yield node, h
    for child in ast.iter_child_nodes(node):
        yield from preorder(child, h+1)


def has_depth_at_least(root, max_depth):
    return any(depth >= max_depth for _, depth in preorder(root))


def name_dump(root):
    return ' '.join(node.__class__.__name__ for node, _ in preorder(root))


class ASTTokenizer:
    def __init__(self, **dump_options):
        self.dump_options = dump_options

    def __call__(self, source_string):
        yield from dump(ast.parse(source_string), **self.dump_options)


def dump(node, annotate_fields=True, include_attributes=False,
         drop_field_names=None, drop_field_values=None, max_depth=None,
         tokenize_leaves=True):
    """
    Adapted from ast.dump, original: https://github.com/python/cpython/blob/master/Lib/ast.py#L88
    """
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
    yield _format(node, 0)
    for subtree, _ in preorder(node):
        if not tokenize_leaves and not has_depth_at_least(subtree, 1):
            continue
        yield _format(subtree, 0)

