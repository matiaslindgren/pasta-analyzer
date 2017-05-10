import unittest
import parsers.ast_parser as ast_parser
import ast
import pprint
import importlib


class TestAllScrapedCodeIsValidSyntax(unittest.TestCase):
    pass




class TestTreeSimilarity(unittest.TestCase):

    # def test_identical_module_differing_variable_names(self):
    #     s1 = "def f(a):\n b = 2\n c = 3\n return a + b + c"
    #     s2 = "def g(x):\n y = 2\n z = 3\n return x + y + z"
    #     tree_1 = ast.parse(s1)
    #     tree_2 = ast.parse(s2)
    #     clones = ast_parser.get_subtree_clones(tree_1, tree_2)
    #     print("found {} clones".format(len(clones)))

    # def test_two_identical_functions_differing_variable_names(self):
    #     s1 = "class A:\n def __init__(self):\n  self.a = None\n\ndef g(x):\n y = 2\n z = 3\n return x + y + z"
    #     s2 = "def g(x):\n y = 2\n z = 3\n return x + y + z"
    #     tree_1 = ast.parse(s1)
    #     tree_2 = ast.parse(s2)
    #     clones = ast_parser.get_subtree_clones(tree_1, tree_2)
    #     print("found {} clones:".format(len(clones)))
    #     for c in clones:
    #         print(ast_parser.name_dump(c))

    def test_small(self):
        s1 = r"""import os, argparse
defaults = {'color': 'red', 'user': 'guest'}
parser = argparse.ArgumentParser()
parser.add_argument('-u', '--user')
parser.add_argument('-c', '--color')
namespace = parser.parse_args()
command_line_args = {k:v for k, v in vars(namespace).items() if v}
combined = ChainMap(command_line_args, os.environ, defaults)
print(combined['color'])
print(combined['user'])"""
        s2 = "command_line_args = {k:v for k, v in vars(namespace).items() if v}"
        tree_1 = ast.parse(s1)
        tree_2 = ast.parse(s2)
        clones = ast_parser.get_subtree_clones(tree_1, tree_2)
        print("found {} clones:".format(len(clones)))
        for c, _ in clones.values():
            print(ast_parser.name_dump(c))
            print()
        ast_parser.prune_clones(clones)
        print("pruned down to {} clones".format(len(clones)))
        for c, _ in clones.values():
            print(ast_parser.name_dump(c))
            print()

    # def test_two_large_equal_modules(self):
    #     inspect = importlib.import_module("inspect")
    #     print("importing")
    #     inspect_source = inspect.getsource(inspect)
    #     s1 = "class A:\n def __init__(self):\n  self.a = None\n\ndef g(x):\n y = 2\n z = 3\n return x + y + z"
    #     print("parsing 1")
    #     tree_1 = ast.parse(inspect_source)
    #     print("parsing 2")
    #     tree_2 = ast.parse(s1)
    #     print("get clones")
    #     clones = ast_parser.get_subtree_clones(tree_1, tree_2)
    #     print("found {} clones".format(len(clones)))
    #     print("pruning")
    #     pruned = ast_parser.prune_clones(clones)
    #     print("pruned down to {} clones".format(len(pruned)))

if __name__ == "__main__":
    unittest.main(verbosity=2)

