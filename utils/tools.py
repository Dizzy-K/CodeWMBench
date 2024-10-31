import json
from collections import defaultdict

def count_effective_lines_of_code(json_obj):
    # 记录有效行数（去除注释）
    effective_lines = 0
    inside_block_comment = False
    inside_triple_quote = False
    code_lines = json_obj['code'].split('\n')
    code_type = json_obj['type']

    for line in code_lines:
        stripped_line = line.strip()

        if code_type == 'Python':
            if inside_triple_quote:
                if stripped_line.endswith('"""') or stripped_line.endswith("'''"):
                    inside_triple_quote = False
                continue
            elif stripped_line.startswith('"""') or stripped_line.startswith("'''"):
                inside_triple_quote = True
                if stripped_line.count('"""') == 2 or stripped_line.count("'''") == 2:  # Single-line triple quote
                    inside_triple_quote = False
                continue

        if code_type in ['Cpp', 'Java']:
            if inside_block_comment:
                if '*/' in stripped_line:
                    inside_block_comment = False
                    if stripped_line.endswith('*/'):
                        continue
                else:
                    continue
            elif '/*' in stripped_line:
                inside_block_comment = True
                if '*/' in stripped_line:  # Single-line block comment
                    inside_block_comment = False
                    continue

        # Skip single line comments and empty lines
        if code_type == 'Python' and stripped_line.startswith('#') or \
           code_type in ['C++', 'Java'] and stripped_line.startswith('//') or \
           stripped_line == '':
            continue

        effective_lines += 1

    return effective_lines

if __name__ == '__main__':
    input_ = "/home/dizzylong/work/lab/TETC/datagen/data/Code*Net1.jsonl"
    step=10
    with open(input_, 'r', encoding='utf-8') as file:
        data = [json.loads(line) for line in file]
    samples_count = defaultdict(list)
    for json_obj in data:
        # if not isinstance(samples_count[str(json_obj['type']+('-fine' if json_obj['test_case'] else '-coarse'))], list):
        #     samples_count[str(json_obj['type']+('-fine' if json_obj['test_case'] else '-coarse'))] = []
        samples_count[str(json_obj['type']+('-fine' if json_obj['test_case'] else '-coarse'))].append(count_effective_lines_of_code(json_obj))
    
    counts = defaultdict(int)
    for key in samples_count.keys():
        for item in samples_count[key]:
            start = (item - 1) // step * step + 1
            end = start + step - 1
            group = f"{start}-{end}"
            counts[f"{key}-{group}"] += 1
    print(counts)
