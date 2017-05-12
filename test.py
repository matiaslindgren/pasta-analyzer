import unittest
import parsers.ast_parser as ast_parser
import ast
import pprint
import importlib


class TestAllScrapedCodeIsValidSyntax(unittest.TestCase):
    pass




class TestTreeSimilarity(unittest.TestCase):

    def _test_ast_parser(self, string1, string2):
        print()
        tree_1 = ast.parse(string1)
        tree_2 = ast.parse(string2)
        source1_linenos, source2_linenos = ast_parser.get_similar_lines(tree_1, tree_2)
        print()
        print("found {} clones".format(len(source2_linenos)))
        print("source1:")
        for n, line in enumerate(string1.splitlines(), start=1):
            print(line + (" <<" if n in source1_linenos else ""))
        print("-"*30)
        print("source2:")
        for n, line in enumerate(string2.splitlines(), start=1):
            print(line + (" <<" if n in source2_linenos else ""))
        print()

    def _test_1(self):
        s1 = "def f(a, b, *args, c=0, d=None, e=tuple(), **kwargs):\n b += 2\n c += 3\n return e[0]"
        s2 = "def g_function(pos_arg1, pos_arg_a, *xs, i=0, nothing=None, default=tuple(), **more_kwargs):\n x = 2\n c = None\n return x + c"
        self._test_ast_parser(s1, s2)

    def test_2(self):
        s1 = "def f(a):\n b = 2\n c = 3\n return a + b + c"
        s2 = "def g(x):\n y = 2\n z = 3\n return x + y + z"
        self._test_ast_parser(s1, s2)

    def _test_3(self):
        s1 = "class A:\n def __init__(self):\n  self.a = None\n\ndef g(x):\n y = 2\n z = 3\n return x + y + z"
        s2 = "def g(x):\n y = 2\n z = 3\n return x + y + z"
        self._test_ast_parser(s1, s2)

    def _test_4(self):
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
        self._test_ast_parser(s1, s2)

    def _test_5(self):
        s1 = "a, b = 0, 1"
        # s1 = "a, b = b, a+b"
        s2 = """# Fibonacci numbers module

def fib(n):    # write Fibonacci series up to n
    a, b = 0, 1
    while b < n:
        print(b, end=' ')
        a, b = b, a+b
    print()

def fib2(n):   # return Fibonacci series up to n
    result = []
    a, b = 0, 1
    while b < n:
        result.append(b)
        a, b = b, a+b
    return result
"""
        self._test_ast_parser(s1, s2)

    # def _test_two_large_equal_modules(self):
    #     inspect = importlib.import_module("inspect")
    #     print("importing")
    #     inspect_source = inspect.getsource(inspect)
    #     self._test_ast_parser(inspect_source, inspect_source)


if __name__ == "__main__":
    unittest.main(verbosity=2)

