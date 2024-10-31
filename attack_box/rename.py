import re
import random
import string
import json
from tqdm import tqdm
from copy import deepcopy
import ast
import builtins


def process_python_function_bak(function_code):
    """ Process a single function's code to replace variable and function names in Python. """
    # Python keywords
    python_keywords = {
        'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await', 'break', 'class',
        'continue', 'def', 'del', 'elif', 'else', 'except', 'finally', 'for', 'from', 'global',
        'if', 'import', 'in', 'is', 'lambda', 'nonlocal', 'not', 'or', 'pass', 'raise',
        'return', 'try', 'while', 'with', 'yield'
    }
    python_keywords.update(dir(builtins))
    # Regular expression pattern for identifying variables and function names
    pattern = r'\bdef\s+([a-zA-Z_][\w]*)\b|\b([a-zA-Z_][\w]*)\b'

    name_mapping = {}

    # Function to replace each match with a unique random string
    def replace(match):
        if match.group(1):  # Function name
            original_name = match.group(1)
        elif match.group(2):  # Variable name
            original_name = match.group(2)
        else:
            return match.group(0)

        # Check if name is a Python keyword or already processed
        if original_name in python_keywords or original_name in name_mapping:
            return match.group(0)

        # Generate a new random name and save it in the mapping
        new_name = generate_random_string()
        name_mapping[original_name] = new_name
        return new_name

    # First pass: identify all names and generate new names
    re.sub(pattern, replace, function_code)

    # Second pass: replace all occurrences of the names
    for original_name, new_name in name_mapping.items():
        function_code = re.sub(r'\b{}\b'.format(original_name), new_name, function_code)

    return function_code

def generate_random_string(length=5):
    """ Generate a random string of fixed length. """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

def process_cpp_function(function_code):
    """ Process a single function's code to replace parameter and variable names in C++. """
    # C++ keywords
    cpp_keywords = {
        "alignas", "alignof", "and", "and_eq", "asm", "auto", "bitand", "bitor", "bool", "break",
        "case", "catch", "char", "char16_t", "char32_t", "class", "compl", "const", "constexpr",
        "const_cast", "continue", "decltype", "default", "delete", "do", "double", "dynamic_cast",
        "else", "enum", "explicit", "export", "extern", "false", "float", "for", "friend", "goto",
        "if", "inline", "int", "long", "mutable", "namespace", "new", "noexcept", "not", "not_eq",
        "nullptr", "operator", "or", "or_eq", "private", "protected", "public", "register",
        "reinterpret_cast", "return", "short", "signed", "sizeof", "static", "static_assert",
        "static_cast", "struct", "switch", "template", "this", "thread_local", "throw", "true",
        "try", "typedef", "typeid", "typename", "union", "unsigned", "using", "virtual", "void",
        "volatile", "wchar_t", "while", "xor", "xor_eq"}

    # Split the function into header and body
    pattern = r'\b(?:int|float|double|char|bool|void|auto|std::\w+)[&*]*\s+([a-zA-Z_][\w]*)\b'
    all_identifiers = re.findall(pattern, function_code)

    # Replace each identifier name in the code
    for identifier in set(all_identifiers):
        if identifier not in cpp_keywords and identifier != "main":
            random_string = generate_random_string()
            function_code = re.sub(r'\b' + identifier + r'\b', random_string, function_code)

    return function_code

def process_java_function(function_code):
    """ Process a single function's code to replace parameter and variable names. """
    # Split the function into header and body
    header_match = re.match(r'(.*?\()([^)]*\))(.*)', function_code, re.DOTALL)
    java_keywords = {
        "abstract", "assert", "boolean", "break", "byte", "case", "catch", "char", "class", "const",
        "continue", "default", "do", "double", "else", "enum", "extends", "final", "finally", "float",
        "for", "goto", "if", "implements", "import", "instanceof", "int", "interface", "long", "native",
        "new", "package", "private", "protected", "public", "return", "short", "static", "strictfp", "super",
        "switch", "synchronized", "this", "throw", "throws", "transient", "try", "void", "volatile", "while"}
    if header_match:
        function_start, function_header, function_body = header_match.groups()
        # Modify regex to include generic types and for loop variables
        all_identifiers = re.findall(r'\b[a-zA-Z_][\w<>?]*\s+([a-zA-Z_][\w]*)\b', function_header)
        all_identifiers += re.findall(r'for\s*\(\s*[a-zA-Z_][\w<>?]*\s+([a-zA-Z_][\w]*)\s*:', function_body)
    
        # Replace each identifier name in both header and body
        for identifier in set(all_identifiers):
            if identifier not in java_keywords:
                random_string = generate_random_string()
                function_header = re.sub(r'\b' + identifier + r'\b', random_string, function_header)
                function_body = re.sub(r'\b' + identifier + r'\b', random_string, function_body)

        return function_start + function_header + function_body
    else:
        return function_code

def process_python_function_bak(function_code):
    """ Process a single function's code to replace variable and function names in Python. """
    # Python keywords
    python_keywords = {
    # Python 关键字
    'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await', 'break', 'class',
    'continue', 'def', 'del', 'elif', 'else', 'except', 'finally', 'for', 'from', 'global',
    'if', 'import', 'in', 'is', 'lambda', 'nonlocal', 'not', 'or', 'pass', 'raise',
    'return', 'try', 'while', 'with', 'yield',

    # 常用内置函数
    'abs', 'divmod', 'input', 'open', 'staticmethod', 'all', 'enumerate', 'int', 'ord', 
    'str', 'any', 'eval', 'isinstance', 'pow', 'sum', 'basestring', 'execfile', 'issubclass', 
    'print', 'super', 'bin', 'file', 'iter', 'property', 'tuple', 'bool', 'filter', 'len', 
    'range', 'type', 'bytearray', 'float', 'list', 'raw_input', 'unichr', 'callable', 'format', 
    'locals', 'reduce', 'unicode', 'chr', 'frozenset', 'long', 'reload', 'vars', 'classmethod', 
    'getattr', 'map', 'repr', 'xrange', 'cmp', 'globals', 'max', 'reversed', 'zip', 'compile', 
    'hasattr', 'memoryview', 'round', '__import__', 'complex', 'hash', 'min', 'set', 'delattr', 
    'help', 'next', 'setattr', 'dict', 'hex', 'object', 'slice', 'dir', 'id', 'oct', 'sorted',

    # 常用方法和参数
    'append', 'end', 'sort', 'reverse', 'insert', 'remove', 'pop', 'clear', 'extend', 'index',
    'count', 'copy', 'join', 'sep', 'split', 'strip', 'find', 'replace', 'read', 'write', 'close',

    # 常见标准库模块名
    'os', 'sys', 'math', 'random', 'datetime', 'json', 're', 'collections', 'functools', 
    'itertools', 'heapq', 'bisect', 'copy', 'pickle', 'csv', 'configparser', 'logging', 
    'argparse', 'subprocess', 'threading', 'multiprocessing', 'socket', 'asyncio', 'queue', 
    'select', 'ssl', 'http', 'xml', 'urllib', 'ftplib', 'poplib', 'smtplib', 'sqlite3', 'zlib', 
    'gzip', 'time', 'calendar', 'hashlib', 'base64', 'binascii', 'struct', 'codecs', 'unicodedata', 
    'io'
}


    python_keywords.update(dir(builtins))
    # Regular expression pattern for identifying variables and function names
    pattern = r'\b([a-zA-Z_][\w]*)\b\s*='

    def replace(match):
        original_name = match.group(1)

        if original_name in python_keywords:
            return match.group(0)

        new_name = generate_random_string()
        nonlocal function_code
        function_code = re.sub(r'\b{}\b'.format(original_name), new_name, function_code)
        return new_name

    re.sub(pattern, replace, function_code)
    return function_code


def process_code(code, code_type):
    """ 根据代码类型选择相应的处理函数 """
    if code_type == "C++":
        return process_cpp_function(code)
    elif code_type == "Java":
        return process_java_function(code)
    elif code_type == "Python":
        # return process_python_function(code)
        return process_python_function_bak(code)
    else:
        return None

# input_data_path = "/home/dizzylong/work/lab/opaque_predicate/opaque_predicate_cn_cpp.jsonl"
# input_data_path = "data/insert.jsonl"
input_data_path = "/home/dizzylong/work/lab/output_flan-ul2.jsonl"
with open(input_data_path, 'r') as input_file, open('data/rename_flan.jsonl', 'w') as output_file:
    origin_data = input_file.readlines()
    print(len(origin_data))
    for line in tqdm(origin_data):
        func_info = json.loads(line)
        code = func_info['with_watermark']
        # code_type = func_info['type']
        code_type = 'C++'
        renamed_code = process_code(code, code_type)
        func_info['rename_code'] = renamed_code
        output_file.write(json.dumps(func_info) + '\n')
