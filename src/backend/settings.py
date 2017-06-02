INDEX_DIRNAME = "index"
INDEX_NAME = "simple_index"

TOKENIZER_OPTIONS = {
    # Ignore variable, function, class and argument names
    'drop_field_names': {"id", "arg", "name"},
    # Do not compare the root nodes of two syntax trees
    'drop_node_names': {"Module"},
    # Minimum depth of a matching syntax tree
    'min_depth': 4
}

MAX_LINES_IN_SEARCH_RESULT_CODE_BLOCK = 10

