import os.path

INDEX_DIRNAME = os.path.abspath(os.path.join("src", "backend", "index"))
INDEX_NAME = "simple_index"
INDEX_MAX_SIZE = int(8e9)

TOKENIZER_OPTIONS = {
    # Ignore variable, function, class and argument names.
    'drop_field_names': {"id", "arg", "name"},
    # Do not compare the root nodes of two syntax trees.
    'drop_node_names': {"Module"},
    # Minimum depth of a syntax tree token.
    # 4 is sufficient for matching for example a variable
    # assignment from the result of a function call but not
    # a variable assignment from a literal
    'min_depth': 4
}

# Limit the search result preview blocks' height
MAX_LINES_IN_SEARCH_RESULT_CODE_BLOCK = 10

