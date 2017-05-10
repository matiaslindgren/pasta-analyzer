"""
optimization todo:
    * invent some single sensitivity parameter which cascades everywhere
    * preprocess every ast
    * hash value of a tree node is the string of the nodes attrs concatenated with the ones of its children

"""
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
    def __init__(self, min_depth=1, drop_field_names=None, drop_node_names=None):
        if drop_field_names is None:
            drop_field_names = {"id", "arg", "name"}
        if drop_node_names is None:
            drop_node_names = {"Module"}
        self.min_depth = min_depth
        self.drop_field_names = drop_field_names
        self.drop_node_names = drop_node_names
        self.buckets = collections.defaultdict(list)

    def visit(self, node, parent):
        if not has_depth_at_least(node, self.min_depth):
            return
        if node.__class__.__name__ not in self.drop_node_names:
            yield node, parent
        for _, value in ast.iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast.AST):
                        yield from self.visit(item, node)
            elif isinstance(value, ast.AST):
                yield from self.visit(value, node)

    def partition_tree(self, root):
        root.parent = None
        for node, parent in self.visit(root, None):
            key = dump(node, False, drop_field_names=self.drop_field_names)
            node.parent = parent
            self.buckets[key].append(node)


def tree_similarity(nodes_1, nodes_2):
    """
    Return the tree similarity of two trees using the formula from Baxter et al.
    similarity = 2*S/(2*S + L + R)
    where:
        S = number of shared nodes
        L = number of nodes in sub-tree 1 not in sub-tree 2
        R = number of nodes in sub-tree 2 not in sub-tree 1

    TODO:
        - commutative operators
        - similarity strictness
            things to ignore:
              * names: 'id' (variable), 'name' (function), 'arg' (in argument list)
              * bodies, in functions, for loops etc
    """
    S = len(nodes_1 & nodes_2)
    L = len(nodes_1 - nodes_2)
    R = len(nodes_2 - nodes_1)
    return 2*S/(2*S + L + R)


#TODO: optimize using for example Valientes Chapter 4 Tree Isomorphism
def get_subtree_clones(root_1, root_2, similarity_threshold=0.8):
    def prune_clones(node, clones, key_function):
        # print("pruning from {} clones".format(len(clones)))
        for child in ast.walk(node):
            if key_function(child) in clones:
                # print("delete\n{}\nunder\n{}".format(dump(child), dump(node)))
                del clones[key_function(child)]
        # print("done pruning, {} clones remain".format(len(clones)))
    def all_nodes(root):
        return set(dump(n, drop_field_names={"id", "name", "arg"})  for n, _ in preorder(root))
    def already_included(node, clones):
        for _, clone in clones.items():
            for child in ast.walk(clone):
                if dump(child, drop_field_names={"id","name","arg"}) == dump(node, drop_field_names={"id","name","arg"}):
                    return True
        return False
    clones = dict()
    node_visitor = NodeProcessor(min_depth=2)
    print("partition tree 1")
    node_visitor.partition_tree(root_1)
    print("partition tree 2")
    node_visitor.partition_tree(root_2)
    print("get clones")
    i = 1
    for bucket in node_visitor.buckets.values():
        # print("bucket {} with {} {} nodes and {} combinations".format(i, len(bucket), bucket[0].__class__.__name__, len(tuple(itertools.combinations(bucket, 2)))))
        i+=1
        # Compare every node in the bucket to each other, buckets
        # with one node are ignored
        for node_1, node_2 in itertools.combinations(bucket, 2):
            # print("comparing\n{0}\n{1}\nto\n{3}\n{2}".format(dump(node_1), dump(node_1, drop_field_names={"id", "name","arg"}), dump(node_2, drop_field_names={"id","name","arg"}), dump(node_2)))
            # print("similarity: {}".format(tree_similarity(all_nodes(node_1), all_nodes(node_2))))
            # print("get similarity")
            if tree_similarity(all_nodes(node_1), all_nodes(node_2)) > similarity_threshold:
                # if already_included(node_1, clones) or already_included(node_2, clones):
                    # continue
                # prune_clones(node_1, clones, dump)
                # prune_clones(node_2, clones, dump)
                clones[(dump(node_1), dump(node_2))] = (node_1, node_2)
        # print("currently {} possible clones ".format(len(clones)))
    print("done searching for clones, return")
    return clones


def prune_clones(clones, similarity_threshold=0.7):
    def all_nodes(root):
        return set(dump(n, drop_field_names={"id", "name", "arg"})  for n, _ in preorder(root))
    not_checked = list(clones.values())
    while not_checked:
        print("{} pairs not checked".format(len(not_checked)))
        node_1, node_2 = not_checked.pop()
        if node_1.__class__.__name__ == "Module":
            continue
        parent_1, parent_2 = node_1.parent, node_2.parent
        if tree_similarity(all_nodes(parent_1), all_nodes(parent_2)) > similarity_threshold:
            key = (dump(node_1), dump(node_2))
            if key in clones:
                del clones[key]
            clones[(dump(parent_1), dump(parent_2))] = (parent_1, parent_2)
            not_checked.append((parent_1, parent_2))


def name_dump(root):
    for node, depth in preorder(root):
        print(' '*depth + node.__class__.__name__)


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

