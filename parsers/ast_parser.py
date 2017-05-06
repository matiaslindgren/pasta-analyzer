import ast
import collections
import itertools


def has_children(node):
    return next(ast.iter_child_nodes(node), None) is not None

def dive(node, h):
    yield h
    for child in ast.iter_child_nodes(node):
        yield from dive(child, h+1)


def has_depth_at_least(root, max_depth):
    return any(depth > max_depth for depth in dive(root, 0))


class NodeHasher():
    def __init__(self, min_depth=1, sensitivity=0):
        self.min_depth = min_depth
        self.drop_field_names = self.generate_drop_field_names(sensitivity)

    def generate_drop_field_names(self, sensitivity):
        if sensitivity < 1:
            return {"name", "id"}
        return set()

    def visit(self, node):
        if has_depth_at_least(node, self.min_depth):
            yield node
            for field, value in ast.iter_fields(node):
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, ast.AST):
                            yield from self.visit(item)
                elif isinstance(value, ast.AST):
                    yield from self.visit(value)

    def hashed_nodes(self, root):
        buckets = collections.defaultdict(list)
        for node in self.visit(root):
            buckets[node.__class__.__name__].append(node)
        return buckets


def dump(node, annotate_fields=True, drop_field_names=None):
    """
    Adapted from ast.dump, original: https://github.com/python/cpython/blob/master/Lib/ast.py#L88
    Added an optional drop_field_names set of strings, which can be used to ignore certain node attributes such as variable id's.
    """
    if drop_field_names is None:
        drop_field_names = set()

    def _format(node, level=0):
        if isinstance(node, ast.AST):
            fields = [(a, _format(b, level))
                      for a, b in ast.iter_fields(node)
                      if a not in drop_field_names]
            return ''.join([
                node.__class__.__name__,
                '(',
                ', '.join(('%s=%s' % field for field in fields)
                           if annotate_fields else
                           (b for a, b in fields)),
                ')'])
        elif isinstance(node, list):
            return '[%s]' % ', '.join(map(_format, node))
        return repr(node)

    if not isinstance(node, ast.AST):
        raise TypeError('expected AST, got %r' % node.__class__.__name__)
    return _format(node)


# TODO temporary
def tree_similarity(root_1, root_2):
    depth_1 = max(dive(root_1, 0))
    depth_2 = max(dive(root_2, 0))
    return (depth_1+depth_2)/(2*max(depth_1, depth_2))


def get_subtree_clones(root, similarity_threshold=0.5):
    def prune_clones(node, as_key):
        for child in ast.walk(node):
            if child in clones:
                del clones[as_key(child)]
    clones = dict()
    node_visitor = NodeHasher()
    for bucket in node_visitor.hashed_nodes(root).values():
        for node_1, node_2 in itertools.combinations(bucket, 2):
            print(node_1, node_2)
            if tree_similarity(node_1, node_2) > similarity_threshold:
                prune_clones(node_1, dump)
                prune_clones(node_2, dump)
                clones[dump(node_1)] = node_1
                clones[dump(node_2)] = node_2
    return set(clones.keys())

# similarity = 2*shared_nodes/(2*shared_nodes + different_nodes(tree_1) + different_nodes(tree_2))
# mass_threshold = some_constant # amount of nodes

# enhancements:
# semantic equality,
# commutative operators

# INITIAL PSEUDO -> PYTHON MESS:
#
# 1. iterate all subtrees and find clones:

#
#

# 2. sequence detection:
#
# build list structures with sequences
# for k in range(minseqlen, maxseqlen+1):
#   place subseqs of len k into buckets
# for bucket in buckets:
#   for seq_1 in bucket:
#     for seq_2 in bucket:
#       if seq_1 == seq_2:
#         continue
#       if compare_seqs(seq_1, seq_2, k) > similarity_threshold:
#         remove_seq_subclones(clones, seq_1, seq_2, k)
#         add_seq_clone_pair(clones, seq_1, seq_2, k)

# 3. generalization of clones by checking parent:
#
# clones_to_gen = clones # set
# while clones_to_gen:
#   remove clone(i, j) from clones_to_gen
#   if compare_clones(parentof(i), parentof(j)) > similarity_threshold:
#     removeclonepair(clones, i, j)
#     addclonepair(clones, parentof(i), parentof(j))
#     addclonepair(clones_to_gen, parentof(i), parentof(j))
#
#


