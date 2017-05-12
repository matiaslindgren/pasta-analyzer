import unittest
import parsers.ast_parser as ast_parser


class TestTreeSimilarity(unittest.TestCase):

    def _dump_with_similar_lines(self, string1, string2, lines1, lines2):
        msg = "\nSource 1:\n\n"
        for n, line in enumerate(string1.splitlines(), start=1):
            msg += line + (" <<" if n in lines1 else "") + "\n"
        msg += "\nCompared to source 2:\n\n"
        for n, line in enumerate(string2.splitlines(), start=1):
            msg += line + (" <<" if n in lines2 else "") + "\n"
        return msg + "\n"

    def test_only_function_signature_equal(self):
        s1 = "def f(a, b, *args, c=0, d=None, e=tuple(), **kwargs):\n b += 2\n c += 3\n return e[0]"
        s2 = "def g_function(pos_arg1, pos_arg_a, *xs, i=0, nothing=None, default=tuple(), **more_kwargs):\n x = 2\n c = None\n return x + c"
        lines_1, lines_2 = ast_parser.get_similar_lines(s1, s2)
        msg = self._dump_with_similar_lines(s1, s2, lines_1, lines_2) + "Function signature should be similar"
        self.assertIn(1, lines_1, msg)
        self.assertIn(1, lines_2, msg)

    def test_equal_functions(self):
        s1 = "def f(a):\n b = 2\n c = 3\n return a + b + c"
        s2 = "def g(x):\n y = 2\n z = 3\n return x + y + z"
        lines_1, lines_2 = ast_parser.get_similar_lines(s1, s2)
        msg = self._dump_with_similar_lines(s1, s2, lines_1, lines_2) + "All lines should be equal"
        for line in range(1, len(s1.splitlines())+1):
            self.assertIn(line, lines_1, msg)
            self.assertIn(line, lines_2, msg)


if __name__ == "__main__":
    unittest.main(verbosity=2)

