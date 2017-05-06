import ast


def has_children(node):
    return next(ast.iter_child_nodes(node), None) is not None

def dive(node, h):
    yield node, h
    for child in ast.iter_child_nodes(node):
        yield from dive(child, h+1)

def has_depth_at_least(root, max_depth):
    return any(depth for _, depth in dive(root, 0) if depth > max_depth)

class NodeHasher(ast.NodeVisitor):
    def __init__(self, min_depth=1, sensitivity=1):
        self.min_depth = min_depth
        self.drop_field_names = self.generate_drop_field_names(sensitivity)

    def generate_drop_field_names(self, sensitivity):
        if sensitivity < 1:
            return {"name", "id"}
        return set()

    def visit(self, node):
        if has_depth_at_least(node, self.min_depth):
            # change print to hash
            print(dump(node, False, self.drop_field_names), end="\n\n")
            self.generic_visit(node)



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


# similarity = 2*shared_nodes/(2*shared_nodes + different_nodes(tree_1) + different_nodes(tree_2))
# mass_threshold = some_constant # amount of nodes

# enhancements:
# semantic equality,
# commutative operators

# INITIAL PSEUDO -> PYTHON MESS:
#
# 1. iterate all subtrees and find clones:

#
# clones = set()
# hash_table = table()
# for subtree in tree.all_subtrees():
#   if not too_big(subtree, mass_threshold):
#     # trees which are similar: (tree % identifiers) -> same bin (wat?)
#     hash_table.add_to_bucket(subtree)
# for bucket in hash_table.buckets():
#   for subtree_1 in bucket:
#     for subtree_2 in bucket:
#       if subtree_1 == subtree_2:
#         continue
#       if compare_trees(subtree_1, subtree_2) > similarity_threshold:
#         for sub in subtree_1.all_subtrees():
#           if sub in clones:
#             clones.remove_pair(sub)
#         for sub in subtree_2.all_subtrees():
#           if sub in clones:
#             clones.remove_pair(sub)
#         clones.add((subtree_1, subtree_2))
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


