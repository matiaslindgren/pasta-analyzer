import ast
import collections
import itertools


def preorder(node, h=0):
    yield node, h
    for child in ast.iter_child_nodes(node):
        yield from preorder(child, h+1)


def has_depth_at_least(root, max_depth):
    return any(depth > max_depth for _, depth in preorder(root))


class NodeProcessor():
    """
    Preprocess ASTs by grouping subtrees together that are similar when their string dumps are compared.
    The similarity threshold can be controlled by altering the drop_field_names set.
    """
    def __init__(self, min_depth=1, drop_field_names=None, drop_node_names=None):
        if drop_field_names is None:
            drop_field_names = {"id", "arg", "name"}
        if drop_node_names is None:
            drop_node_names = {"Module"}
        self.min_depth = min_depth
        self.drop_field_names = drop_field_names
        self.drop_node_names = drop_node_names
        self.buckets = collections.defaultdict(list)

    def visit(self, node):
        if not has_depth_at_least(node, self.min_depth):
            return
        if node.__class__.__name__ not in self.drop_node_names:
            yield node
        for _, value in ast.iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast.AST):
                        yield from self.visit(item)
            elif isinstance(value, ast.AST):
                yield from self.visit(value)

    def add_tree(self, root):
        for node in self.visit(root):
            if not hasattr(node, "short_key"):
                node.short_key = dump(node, True)
            if not hasattr(node, "root_node"):
                node.root_node = root
            self.buckets[node.short_key].append(node)

    def get_sorted_buckets(self):
        def longest_node_key_length(bucket):
            return max(map(lambda node: len(node.short_key), bucket))
        sorted_buckets = list(b for b in self.buckets.values() if len(b) > 1)
        sorted_buckets.sort(key=longest_node_key_length, reverse=True)
        return sorted_buckets


def add_all_children_linenumbers(node, linenumber_set):
    for child in ast.walk(node):
        if hasattr(child, "lineno") and child.lineno not in linenumber_set:
            linenumber_set.add(child.lineno)


def get_similar_lines(source_1, source_2, min_depth=2):
    """
    Compare two source strings to each other and get return the line numbers of similar lines.
    Specify min_depth to control the granularity of comparing lines for similarity.
    Higher values match only larger constructs.
    """
    root_1 = ast.parse(source_1)
    root_2 = ast.parse(source_2)
    node_processor = NodeProcessor(min_depth=min_depth)
    node_processor.add_tree(root_1)
    node_processor.add_tree(root_2)
    matched_linenumbers_1 = set()
    matched_linenumbers_2 = set()
    added_keys = ''
    for bucket in node_processor.get_sorted_buckets():
        for node_1, node_2 in itertools.combinations(bucket, 2):
            # Don't compare nodes in the same tree
            if node_1.root_node is node_2.root_node:
                continue
            # Add linenumbers of all lines in subtrees of the matched nodes
            if node_1.short_key not in added_keys:
                add_all_children_linenumbers(node_1, matched_linenumbers_1)
            if node_2.short_key not in added_keys:
                add_all_children_linenumbers(node_2, matched_linenumbers_2)
            if node_1.short_key not in added_keys:
                added_keys += "\n{}\n".format(node_1.short_key)
            if node_2.short_key not in added_keys:
                added_keys += "\n{}\n".format(node_2.short_key)
    return matched_linenumbers_1, matched_linenumbers_2


def name_dump(root):
    for node, depth in preorder(root):
        print(' '*depth + node.__class__.__name__ + ",".join(map(str, ast.iter_fields(node))))


def dump(node, annotate_fields=True, include_attributes=False, drop_field_names=None):
    """
    Adapted from ast.dump, original: https://github.com/python/cpython/blob/master/Lib/ast.py#L88
    Added an optional drop_field_names set of strings, which can be used to ignore certain node attributes such as variable id's.
    """
    if drop_field_names is None:
        drop_field_names = set()
    def _format(node):
        if isinstance(node, ast.AST):
            fields = [(a, _format(b))
                      for a, b in ast.iter_fields(node)
                      if a not in drop_field_names]
            rv = '%s(%s' % (node.__class__.__name__, ', '.join(
                ('%s=%s' % field for field in fields)
                if annotate_fields else
                (b for a, b in fields)
            ))
            if include_attributes and node._attributes:
                rv += fields and ', ' or ' '
                rv += ', '.join('%s=%s' % (a, _format(getattr(node, a)))
                                for a in node._attributes)
            return rv + ')'
        elif isinstance(node, list):
            return '[%s]' % ', '.join(map(_format, node))
        return repr(node)
    if not isinstance(node, ast.AST):
        raise TypeError('expected AST, got %r' % node.__class__.__name__)
    return _format(node)

