import glob
from codebleubase import *
import numpy as np
from collections import Counter
from tqdm import tqdm
import json
import re


def calculate_codebleu(text1, text2, lang, params):
    alpha, beta, gamma, theta = [float(x) for x in params.split(',')]

    # preprocess inputs
    hypothesis = text1.split('\n')
    references = [text2.split('\n')]
    ngram_match_score = bleu.corpus_bleu([[hypothesis]], references)
    
    keywords = [x.strip() for x in open('keywords/'+lang+'.txt', 'r', encoding='utf-8').readlines()]
    def make_weights(reference_tokens, key_word_list):
        return {token:1 if token in key_word_list else 0.2 for token in reference_tokens}
    tokenized_refs_with_weights = [[[reference_tokens, make_weights(reference_tokens, keywords)] for reference_tokens in reference] for reference in references]

    weighted_ngram_match_score = weighted_ngram_match.corpus_bleu([references], [hypothesis])
    

    # calculate syntax match
    syntax_match_score = syntax_match.corpus_syntax_match([[text2]], [text1], lang)
    
    # calculate dataflow match
    dataflow_match_score = dataflow_match.corpus_dataflow_match([[text2]], [text1], lang)
    
    code_bleu_score = alpha*ngram_match_score + beta*weighted_ngram_match_score + gamma*syntax_match_score + theta*dataflow_match_score
    return code_bleu_score

def process_target(target):
    if type(target) == list:
        pattern = r"```[a-zA-Z]{0,10}\n(.*?)```"
        for i in target:
            match = re.findall(pattern, i, re.DOTALL)
            if match:
                target = match[0]
                break
    return target

def calculate_codebleu_single_file(input_file):
    langs = {'C++':'cpp', 'Java':'java', 'Python':'python'}
    codebleu = {'fine_C++': [], 'fine_Python': [], 'fine_Java': [], 'coarse_C++': [], 'coarse_Python': [], 'coarse_Java': []}
    params = '0.25,0.25,0.25,0.25'
    
    with open(input_file, 'r') as file:
        for line in tqdm(file, desc='Calculating CodeBleu'):
            json_obj = json.loads(line)
            lang = langs[json_obj['type']]
            source = json_obj['code']
            target = process_target(json_obj.get('wm') or json_obj.get('wmname') or json_obj.get('opaque_predicate'))
            if not target:
                continue

            prefix = 'fine_' if 'test_case' in json_obj else 'coarse_'
            key = prefix + lang
            codebleu_score = calculate_codebleu(source, target, lang, params)
            codebleu[key].append(codebleu_score)

    return codebleu

def calculate_codebleu_dual_files(file1, file2, flag1, flag2):
    langs = {'C++':'cpp', 'Java':'java', 'Python':'python'}
    codebleu = {'C++': [], 'Java': [], 'Python': []}
    params = '0.25,0.25,0.25,0.25'
    
    with open(file1, 'r') as f1:
        for line in f1:
            json_obj = json.loads(line)
            data1[json_obj['id']] = json_obj

    # 读取第二个文件，按 id 存入字典
    with open(file2, 'r') as f2:
        for line in f2:
            json_obj = json.loads(line)
            data2[json_obj['id']] = json_obj

    # 对齐并计算 CodeBLEU 分数
    matched_ids = set(data1.keys()) & set(data2.keys())
    for id in tqdm(matched_ids, desc='Calculating CodeBleu for Matched IDs'):
        json_obj1 = data1[id]
        json_obj2 = data2[id]

        lang1 = langs[json_obj1['type']]
        lang2 = langs[json_obj2['type']]

        # 确保语言类型相同
        if lang1 != lang2:
            continue
        
        source = json_obj1['code']
        target = json_obj2['code']
        
        codebleu_score = calculate_codebleu(source, target, lang1, params)
        codebleu[lang1].append(codebleu_score)
    
    for lang, scores in codebleu.items():
        if scores:  # 确保列表不为空
            average_score = sum(scores) / len(scores)
            print(f"Language: {lang}, Average CodeBleu Score: {average_score:.2f}")
    return codebleu

if __name__ == '__main__':
    input_file1 = '/home/dizzylong/work/lab/final/data/retrans_ins.jsonl'
    input_file2 = '/home/dizzylong/work/lab/final/data/retrans_ins.jsonl'
    
    codebleu = calculate_codebleu_dual_files(input_file1, input_file2, 'code', 'code')

    for category, scores in codebleu.items():
        if scores:  # 确保列表不为空
            rounded_scores = np.round(scores, decimals=1)
            frequency = Counter(rounded_scores)

            # 打印每个类别的四舍五入后的频率分布
            print(f"Category: {category}")
            for key in sorted(frequency):
                print(f"  {key}: {frequency[key]}")

            # 计算并打印每个类别的平均值
            avg_score = sum(scores) / len(scores)
            print(f"  Average Score: {avg_score:.2f}\n")

    # 计算所有类别的总平均值
    all_scores = [score for scores in codebleu.values() for score in scores]
    if all_scores:  # 确保列表不为空
        total_avg = sum(all_scores) / len(all_scores)
        print(f"Overall Average CodeBleu: {total_avg:.2f}")
    # codebleu.append(calculate_cpp_codebleu(line, matches[0], lang, params))
    
# with open('/home/dizzylong/work/code-to-code-trans/retranslate_csn_java/test_0.output', 'r') as f1, open('/home/dizzylong/work/code-to-code-trans/retranslate_csn_cs/test_0.source', 'r') as f2:
#     codebleu = {'coarse_java': [], 'fine_Python': [], 'fine_Java': [], 'coarse_C++': [], 'coarse_Python': [], 'coarse_Java': []}
#     targets = f1.readlines()
#     sources = f2.readlines()
#     lang = 'java'
#     params = '0.25,0.25,0.25,0.25'
#     prefix = 'coarse_'
#     for i, target in enumerate(tqdm(targets)):
#         source = sources[i]
#         key = prefix + 'Java'
#         try:
#             # 假设 calculate_codebleu 返回一个数值
#             codebleu_score = calculate_codebleu(source, target, lang, params)
#             codebleu[key].append(codebleu_score)
#         except TypeError:
#             pass

#     for category, scores in codebleu.items():
#         if scores:  # 确保列表不为空
#             rounded_scores = np.round(scores, decimals=1)
#             frequency = Counter(rounded_scores)

#             # 打印每个类别的四舍五入后的频率分布
#             print(f"Category: {category}")
#             for key in sorted(frequency):
#                 print(f"  {key}: {frequency[key]}")

#             # 计算并打印每个类别的平均值
#             avg_score = sum(scores) / len(scores)
#             print(f"  Average Score: {avg_score:.2f}\n")

#     # 计算所有类别的总平均值
#     all_scores = [score for scores in codebleu.values() for score in scores]
#     if all_scores:  # 确保列表不为空
#         total_avg = sum(all_scores) / len(all_scores)
#         print(f"Overall Average CodeBleu: {total_avg:.2f}")
#     # codebleu.append(calculate_cpp_codebleu(line, matches[0], lang, params))
