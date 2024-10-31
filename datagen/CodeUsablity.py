# main.py
import os
import json
from tqdm import tqdm
import subprocess
import execjs
from collections import defaultdict
from tree_sitter import Language, Parser
import ast
import random

class SyntaxChecker:
    def __init__(self):
        self.JAVA_LANGUAGE = Language('parser/my-languages.so', 'java')
        self.parser = Parser()
        self.parser.set_language(self.JAVA_LANGUAGE)

    def check_syntax(self, json_obj, lang, flag='code'):
        code = json_obj[flag]
        if lang == "Java":
            tree = self.parser.parse(bytes(code, "utf8"))
            return self.check_java_syntax(tree.root_node)
        elif lang == "Python":
            return self.check_python_syntax(code)
        elif lang == "C++":
            return self.check_cpp_syntax(code)
        else:
            return False, "Language not supported."

    def check_java_syntax(self, node):
        if node.has_error:
            return False, "Syntax error found in Java code."
        for child in node.children:
            result, message = self.check_java_syntax(child)
            if not result:
                return result, message
        return True, "No syntax errors found in Java code."

    def check_python_syntax(self, code):
        try:
            ast.parse(code)
            return True, "No syntax errors found in Python code."
        except SyntaxError as e:
            return False, f"Syntax error in Python code: {e}"

    def check_cpp_syntax(self, code):
        with open('temp.cpp', 'w') as file:
            file.write(code)
        result = subprocess.run(["g++", "-fsyntax-only", "temp.cpp"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            return True, "No syntax errors found in C++ code."
        else:
            return False, f"Syntax error in C++ code: {result.stderr.decode()}"

class ExecuteChecker:
    def __init__(self):
        pass

    def run_code(self, json_obj, lang, flag='code'):
        if lang == "C":
            return self.handle_c(json_obj, flag)
        elif lang == "Python":
            return self.handle_python(json_obj, flag)
        elif lang == "C++":
            return self.handle_cpp(json_obj, flag)
        elif lang == "JavaScript":
            return self.handle_js(json_obj, flag)
        else:
            return False, "Unsupported language"

    def handle_c(self, json_obj, flag='code'):
        code, binary_path, io_data = json_obj[flag], './temp', json_obj['test_case']
        with open("temp.c", "w", encoding='utf-8') as temp_c_file:
            temp_c_file.write(code)
        for input_data, expected_output in io_data:
            try:
                subprocess.run(['gcc', './temp.c', '-o', binary_path], 
                               stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
                if os.path.exists(binary_path):
                    run_process = subprocess.run([f"./{binary_path}"], input=input_data, text=True, capture_output=True, check=True, timeout=2)
                    return run_process.stdout.strip() == expected_output.strip()
            except Exception as e:
                pass
            finally:
                self.cleanup(['./temp.c', binary_path])
            return False

    def handle_python(self, json_obj, flag='code'):
        code, io_data = json_obj[flag], json_obj['test_case']
        for input_data, expected_output in io_data:
            try:
                run_process = subprocess.run(['python', '-c', code], input=input_data, text=True, capture_output=True, check=True, timeout=2)
                return run_process.stdout.strip() == expected_output.strip()
            except Exception as e:
                pass
        return False

    def handle_cpp(self, json_obj, flag='code'):
        code, binary_path, io_data = json_obj[flag], './temp', json_obj['test_case']
        with open("temp.cpp", "w", encoding='utf-8') as temp_cpp_file:
            temp_cpp_file.write(code)
        for input_data, expected_output in io_data:
            try:
                subprocess.run(['g++', './temp.cpp', '-o', binary_path], 
                               stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
                if os.path.exists(binary_path):
                    run_process = subprocess.run([f"{binary_path}"], input=input_data, text=True, capture_output=True, check=True, timeout=2)
                    return run_process.stdout.strip() == expected_output.strip()
            except Exception as e:
                pass
            finally:
                self.cleanup(['./temp.cpp', binary_path])
            return False

    def handle_js(self, json_obj, flag='code'):
        code = json_obj.get[flag]
        test_cases = json_obj.get("test_case", [])

        ctx = execjs.compile(code)
        for test_input, expected_output in test_cases:
            try:
                actual_output = ctx.eval(f'({test_input})')
                if json.dumps(actual_output) != json.dumps(expected_output):
                    return False
            except:
                return False
        return True

    def cleanup(self, files):
        for file in files:
            if os.path.exists(file):
                os.remove(file)



def code_check(input_file_path, output_file_path, flag='code'):
    with open(input_file_path, 'r') as file, open(output_file_path, 'a') as output_file:
        total = len(file.readlines())
        file.seek(0)
        samples_count = defaultdict(int)
        execc = ExecuteChecker()
        syntaxc = SyntaxChecker()

        # for _ in range(272124):
        #     next(file)
        id_counter = 0

        for line in tqdm(file.readlines(), total=total):
            json_obj = json.loads(line)
            is_usable = False
            type_ = 'Java' if not json_obj.get('type') else json_obj['type']
            # if samples_count[str(type_+('-fine' if json_obj.get('test_case') else '-coarse'))] >= 10000:
            #     continue
            
            if json_obj.get('test_case'):
                is_usable = execc.run_code(json_obj, type_, flag)
            else:
                is_usable = syntaxc.check_syntax(json_obj, type_, flag)

            if is_usable:
                json_obj['id'] = id_counter
                # output_file.write(f"{line}")
                output_line = json.dumps(json_obj) + '\n'
                output_file.write(output_line)
                output_file.flush()
                samples_count[str(type_+('-fine' if json_obj.get('test_case') else '-coarse'))] += 1
                id_counter += 1

        print(samples_count)
# 调用函数

if __name__ == '__main__':
    # folder_path = '/home/dizzylong/work/lab/TETC/CoP/data'
    # for file_name in os.listdir(folder_path):
    #     if file_name.endswith('.jsonl'):
    #         print(file_name)
    #         code_check(os.path.join(folder_path, file_name), '/home/dizzylong/work/lab/TETC/CoP/temp.jsonl', flag='code')
    code_check('/home/dizzylong/work/CoProtector/clean_CSN.jsonl', '/home/dizzylong/work/CoProtector/clean_CSN/final_clean_CSN_all.jsonl', flag='code')
    