import unittest
import sys
import ast
import os.path
sys.path.append(os.path.join(os.path.abspath("."), "backend"))
import json
import tempfile
import random
import indexer
import ast_parser


@unittest.skip("Not implemented")
class TestSpiders(unittest.TestCase):
    # serve python docs at localhost
    # crawl localhost and output to tempfile
    # assert tempfile contains list of data with title, url and snippets
    pass


class TestIndexWriteAndQuery(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open("test/data.json") as f:
            cls.test_data = json.load(f)
        cls.index_dir = tempfile.TemporaryDirectory()
        index_path = os.path.join(cls.index_dir.name, "index")
        cls.index = indexer.Index(index_path, "TEMP_TEST_INDEX")
        for d in cls.test_data:
            cls.index.add_document(d)

    def test_query_with_a_document_from_the_index(self):
        for i in range(10**4):
            data = random.choice(self.test_data)
            for code in data['code_snippets']:
                found = False
                for result in self.index.get_documents(code):
                    if result['title'] == data['title']:
                        found = True
                        break
                self.assertTrue(found, "Pass {}: Did not find result in index even though searched with document that was added into the index\n\nTried to search for:\n{}".format(i+1, code))

    @classmethod
    def tearDownClass(cls):
        cls.index_dir.cleanup()


if __name__ == "__main__":
    unittest.main(verbosity=2)

