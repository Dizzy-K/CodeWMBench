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
import ast
import re



input_data_path = "/home/dizzylong/work/sweet-watermark/sweet_output/generations.json"
todo: str = "retrans"
output_file_path = '/home/dizzylong/work/sweet-watermark/sweet_output/retrans_generations_sweet.json'
load_8bit: bool = False
base_model: str = "/home/dizzylong/work/model/CodeLlama-7b-Instruct-hf"
flag1: str = 'code' # 被重写的标签
flag2: str = 'rewrite' # 目标标签

model, tokenizer = model_init(base_model, load_8bit)

print('load model done...')





with open(input_data_path, 'r') as input_file, open(output_file_path, 'a') as output_file:
    input_file.seek(0)

    lines = input_file.read()
    items = ast.literal_eval(lines)
    max_records = len(items)
    min_records = 0
    print('start')
    # input_file.seek(0)
    execc = ExecuteChecker()
    syntaxc = SyntaxChecker()
    lang = "Python"
    newcodes = []

    for i, line in enumerate(tqdm(items, desc=todo, total=max_records)):

        # json_obj = json.loads(line)
        json_obj = []
        temp = []
        if i < max_records and i >= min_records:
            for item in tqdm(line, desc=todo, total=len(line)):

            # 使用正则表达式查找所有被"""包围的非代码部分
                pattern = r'"""(.*?)"""'
                non_code_segments = re.findall(pattern, item, re.DOTALL)

                # 用非代码段分割文本，提取代码部分
                code_segments = re.split(pattern, item, flags=re.DOTALL)[1:]

                # 每个代码部分与一个非代码部分相交替，从非代码开始
                # 所以要从索引1开始获取代码部分，每两步取一次
                code_segments = code_segments[1::2]

                # 处理每个代码段（比如修改或格式化）
                processed_code_segments = []
                for code in code_segments:
                    # 在这里可以修改每个代码段，比如添加特定功能或格式化
                    # processed_code = rewrite_code(code, lang, tokenizer, model, json_obj)
                    processed_code = retrans_code(code, lang, tokenizer, model, json_obj)
                    processed_code_segments.append(processed_code)

                # 重新构建文本，将修改后的代码放回原位置
                output_text = item
                for original, modified in zip(code_segments, processed_code_segments):
                    output_text = output_text.replace(original, modified, 1)
                temp.append(output_text)
            newcodes.append(temp)
            

        output_file.write(str(newcodes))


print('regen done!')