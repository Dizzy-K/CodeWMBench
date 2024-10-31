# -*- coding: utf-8 -*-

import os
# os.environ["CUDA_VISIBLE_DEVICES"] = "0"
from datagen.CodeUsablity import ExecuteChecker, SyntaxChecker
from attack_box.regen import rewrite_code, model_init, extract_code, retrans_code
import json
from tqdm import tqdm
from copy import deepcopy
from transformers import LlamaForCausalLM, CodeLlamaTokenizer
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import sys
import pickle



input_data_path = "/home/dizzylong/work/CodeMark/dataset/java/CSN_new_b2_100.pickle"
todo: str = "retrans"
output_file_path = 'data/CSN_new_b3_retrans.pickle'
load_8bit: bool = False
base_model: str = "/home/dizzylong/work/model/CodeLlama-7b-Instruct-hf"
flag1: str = 'code' # 被重写的标签
flag2: str = 'rewrite' # 目标标签

model, tokenizer = model_init(base_model, load_8bit)

print('load model done...')



if 'jsonl' in input_data_path:
    try:
        with open(output_file_path, 'r') as output_file1:
            passed_count = len(output_file1.readlines())
            # print('1')
    except FileNotFoundError:
        passed_count = 0
    with open(input_data_path, 'r') as input_file, open(output_file_path, 'a') as output_file:
        input_file.seek(0)
        for _ in range(passed_count):
            next(input_file)

        lines = input_file.readlines()
        max_records = len(lines)
        min_records = 0
        print('start')
        # input_file.seek(0)
        execc = ExecuteChecker()
        syntaxc = SyntaxChecker()
        for i, line in enumerate(tqdm(lines, desc=todo, total=max_records)):

            json_obj = json.loads(line)
            if i < max_records and i >= min_records:
                if flag2 in json_obj:
                    continue
                code_to_rewrite = json_obj[flag1]
                lang = json_obj['type']
                # lang = 'cpp'
                
                if todo == 'deny-rewrite':
                    is_usable = False
                    while not is_usable:
                        rewritten_code = rewrite_code(code_to_rewrite, lang, tokenizer, model, json_obj)
                        temp_obj = deepcopy(json_obj)
                        temp_obj['code'] = extract_code(rewritten_code)[0] if extract_code(rewritten_code) else rewritten_code
                        if temp_obj.get('test_case'):
                            is_usable = execc.run_code(temp_obj, lang)
                        else:
                            is_usable = syntaxc.check_syntax(temp_obj, lang)
                        # if not is_usable:
                        #     print(extract_code(rewritten_code))
                
                elif todo == 'rewrite':
                    rewritten_code = rewrite_code(code_to_rewrite, lang, tokenizer, model, json_obj)

                elif todo == 'retrans':
                    rewritten_code = retrans_code(code_to_rewrite, lang, tokenizer, model, json_obj)

                # if rewritten_code:
                json_obj[flag2] = rewritten_code
                json_obj_str = json.dumps(json_obj)
                output_file.write(json_obj_str + '\n')
            # else:
            #     print(rewritten_code)
else:
    with open(input_data_path, 'rb') as f, open(output_file_path, 'wb') as f2:
        origin_data = pickle.load(f)
        print(len(origin_data))
        func_info = origin_data['all_blobs']
        max_records = len(func_info)
        min_records = 0
        print('start')
        # input_file.seek(0)
        execc = ExecuteChecker()
        syntaxc = SyntaxChecker()
        rewritten_codes = []
        for i, code_to_rewrite in enumerate(tqdm(func_info, desc=todo, total=max_records)):

            # json_obj = json.loads(line)
            if i < max_records and i >= min_records:
                # if flag2 in code_to_rewrite:
                    # continue
                # code_to_rewrite = json_obj[flag1]
                # lang = json_obj['type']
                lang = 'Java'
                json_obj=''
                
                if todo == 'deny-rewrite':
                    is_usable = False
                    while not is_usable:
                        rewritten_code = rewrite_code(code_to_rewrite, lang, tokenizer, model, json_obj)
                        temp_obj = deepcopy(json_obj)
                        temp_obj['code'] = extract_code(rewritten_code)[0] if extract_code(rewritten_code) else rewritten_code
                        if temp_obj.get('test_case'):
                            is_usable = execc.run_code(temp_obj, lang)
                        else:
                            is_usable = syntaxc.check_syntax(temp_obj, lang)
                        # if not is_usable:
                        #     print(extract_code(rewritten_code))
                
                elif todo == 'rewrite':
                    rewritten_code = rewrite_code(code_to_rewrite, lang, tokenizer, model, json_obj)

                elif todo == 'retrans':
                    rewritten_code = retrans_code(code_to_rewrite, lang, tokenizer, model, json_obj)
                rewritten_codes.append(rewritten_code)
                # if rewritten_code:
        origin_data['all_blobs'] = rewritten_codes
        # json_obj_str = json.dumps(json_obj)

        pickle.dump(origin_data, f2)
        # output_file.write(json_obj_str + '\n')

print('regen done!')