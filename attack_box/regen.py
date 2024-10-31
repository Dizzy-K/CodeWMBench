import sys
import os
# os.environ["CUDA_VISIBLE_DEVICES"] = "0"
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2' 
import fire
import torch
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModelForCausalLM, GenerationConfig
from transformers import LlamaForCausalLM, CodeLlamaTokenizer
import subprocess
import glob
import re
import json
# from ..datagen.CodeUsablity import ExecuteChecker, SyntaxChecker
from copy import deepcopy

MAX_INPUT_LEN = 2048 # 4096 8192
if torch.cuda.is_available():
    device = "cuda"
else:
    device = "cpu"

try:
    if torch.backends.mps.is_available():
        device = "mps"
except:
    pass

def evaluate(
        prompts,
        tokenizer,
        model,
        input=None,
        temperature=1,
        do_sample=True,
        top_p=0.95,
        top_k=10,
        num_beams=1,
        max_new_tokens=1024,
        **kwargs,
):
    MAX_INPUT_LEN = 4096
    inputs = tokenizer(prompts, return_tensors="pt", max_length=MAX_INPUT_LEN, truncation=True, padding=False)
    # while inputs["input_ids"].shape[1] == MAX_INPUT_LEN:
    #     MAX_INPUT_LEN += 1024
    #     inputs = tokenizer(prompts, return_tensors="pt", max_length=MAX_INPUT_LEN, truncation=True, padding=False)

    real_prompts = tokenizer.batch_decode(inputs["input_ids"])[0]
    input_ids = inputs["input_ids"].to(device)
    #print("prompts len =",len(prompts),"input_ids shape =",input_ids.shape)
    # if input_ids.shape[1] == MAX_INPUT_LEN:
    #     print("[!] input_ids len == MAX_INPUT_LEN")
    # while inputs["input_ids"].shape[1] == MAX_INPUT_LEN:
    #     MAX_INPUT_LEN += 1024
    #     inputs = tokenizer(prompts, return_tensors="pt", max_length=MAX_INPUT_LEN, truncation=True, padding=False)
    #     real_prompts = tokenizer.batch_decode(inputs["input_ids"])[0]
    #     input_ids = inputs["input_ids"].to(device)

    generation_config = GenerationConfig(
        temperature=temperature,
        do_sample=True,
        top_p=top_p,
        top_k=top_k,
        num_beams=num_beams,
        eos_token_id=tokenizer.eos_token_id,
        pad_token_id=tokenizer.pad_token_id,
        **kwargs,
    )
    with torch.no_grad():
        generation_output = model.generate(
            input_ids=input_ids,
            generation_config=generation_config,
            return_dict_in_generate=True,
            output_scores=True,
            max_new_tokens=max_new_tokens,
        )
    s = generation_output.sequences
    output = tokenizer.batch_decode(s, skip_special_tokens=True)
    return output,real_prompts

def generate_prompt(text, lang, flag='rewrite'):
    PROMPT_TEMPLATES={
        "rewrite": (
            "Below is an instruction that describes a task. "
            "Write a response that appropriately completes the request.\n\n"
            "### Instruction:\n  Here is a {lang} program code. Please rewrite it to enhance its efficiency, readability, and runnability. he revised code should be of the same length (in terms of lines) as the original code. No explanation is needed; only the revised code should be provided. Here's the original code:\n```\n{code}\n```\n\n### Response:"
        ),
        "trans1": (
            "Below is an instruction that describes a task. "
            "Write a response that appropriately completes the request.\n\n"
            "### Instruction:\n Here is a {lang} program code. Please translate it into equivalent {lang2} code. The translated code should maintain the same functionality as the original Java code. No explanation is needed; only the translated C# code should be provided. Here's the original {lang} code:\n```\n{code}\n```\n\n### Response:"
        ),
        "trans2": (
            "Below is an instruction that describes a task. "
            "Write a response that appropriately completes the request.\n\n"
            "### Instruction:\n Here is a {lang2} program code. Please translate it into equivalent {lang} code. The translated code should maintain the same functionality as the original C# code. No explanation is needed; only the translated {lang} code should be provided. Here's the original C# code:\n```\n{code}\n```\n\n### Response:"
        ),
    }
    prompt_template = PROMPT_TEMPLATES[flag]
    if 'trans' in flag:
        lang_dic = {'C++'    : 'Rust',
                  'Java'   : 'Csharp',
                  'Python' : 'Golang'}
        # print(lang_dic[lang])
        return prompt_template.format(lang=lang, code=text, lang2=lang_dic[lang])

    return prompt_template.format(lang=lang, code=text)

def rewrite_code(code, lang, tokenizer, model, json_obj):
    # 生成重写代码的提示
    prompt = generate_prompt(code, lang, flag='rewrite')
    #print(prompt)
    # execc = ExecuteChecker()
    # syntaxc = SyntaxChecker()
    # while True:
    _output, _ = evaluate(prompt, tokenizer, model)
    
    raw_output = _output[0]
    if "### Response:" in raw_output:
        final_output = raw_output.split("### Response:")[1].strip()
    else:
        final_output = raw_output.strip()
    return final_output
        # temp_obj = deepcopy(json_obj)
        # temp_obj['code'] = final_output
        # if temp_obj.get('test_case'):
        #     is_usable = execc.run_code(temp_obj, lang)
        # else:
        #     is_usable = syntaxc.check_syntax(temp_obj, lang)
        
        # if is_usable:
        #     return final_output


def retrans_code(code, lang, tokenizer, model, json_obj):
    # 生成重写代码的提示
    #print(code)
    prompt1 = generate_prompt(code, lang, flag='trans1')
    #print(prompt)
    # execc = ExecuteChecker()
    # syntaxc = SyntaxChecker()
    # while True:
    _output1, _ = evaluate(prompt1, tokenizer, model)
    raw_output1 = _output1[0]
    if "### Response:" in raw_output1:
        final_output1 = raw_output1.split("### Response:")[1].strip()
    else:
        final_output1 = raw_output1
    # pattern = r"```\n(.*?)```"
    # matches1 = re.findall(pattern, final_output1, re.DOTALL)
    matches1 = extract_code(final_output1)
    try:
        newcode = matches1[0]
    except:
        newcode = final_output1
    
    prompt2 = generate_prompt(newcode, lang, flag='trans2')
    
    _output2, _ = evaluate(prompt2, tokenizer, model)
    raw_output2 = _output2[0]
    if "### Response:" in raw_output2:
        final_output2 = raw_output2.split("### Response:")[1].strip()
    else:
        final_output2 = raw_output2
    
    matches2 = extract_code(final_output2)
    try:
        finalcode = matches2[0]
    except:
        finalcode = final_output1
    return finalcode
    
        # temp_obj = deepcopy(json_obj)
        # temp_obj['code'] = final_output
        # if temp_obj.get('test_case'):
        #     is_usable = execc.run_code(temp_obj, lang)
        # else:
        #     is_usable = syntaxc.check_syntax(temp_obj, lang)
        
        # if is_usable:
        #     return final_output
    


def extract_code(text):
    # 匹配三种情况：纯代码、用反引号包裹的代码、带语言指定的代码块
    pattern = r'```[a-z]*\n([\s\S]*?)```|```([\s\S]*?)```'
    matches = re.findall(pattern, text, re.MULTILINE)

    # 清理匹配结果，移除空字符串
    extracted_codes = []
    for match in matches:
        extracted_code = match[0] if match[0] else match[1]
        if extracted_code.strip():
            extracted_codes.append(extracted_code.strip())

    return extracted_codes

def model_init(base_model, load_8bit=False):

    tokenizer = CodeLlamaTokenizer.from_pretrained(base_model)
    tokenizer.pad_token = tokenizer.eos_token
    if device == "cuda":
        model = LlamaForCausalLM.from_pretrained(
            base_model,
            load_in_8bit=load_8bit,
            torch_dtype=torch.float16,
            device_map="auto",
        )
    elif device == "mps":
        model = LlamaForCausalLM.from_pretrained(
            base_model,
            device_map={"": device},
            torch_dtype=torch.float16,
        )

    model.config.pad_token_id = tokenizer.pad_token_id
    if not load_8bit:
        model.half()

    model.eval()
    if torch.__version__ >= "2" and sys.platform != "win32":
        model = torch.compile(model)
    
    return model, tokenizer


def main(
    input_data_path = "/home/dizzylong/work/lab/TETC/datagen/data/Code*Net.jsonl",
    todo: str = "deny-rewrite",
    output_file_path = 'data/rewrite1.jsonl',
    load_8bit: bool = False,
    base_model: str = "/home/dizzylong/work/model/CodeLlama-7b-Instruct-hf",
    flag1: str = 'code', # 被重写的标签
    flag2: str = 'retrans' # 目标标签
):
    assert base_model, (
        "Please specify a --base_model, e.g. --base_model='bigcode/starcoder'"
    )


    model, tokenizer = model_init(base_model, load_8bit)

    with open(input_data_path, 'r') as input_file, open(output_file_path, 'w') as output_file:

        lines = input_file.readlines()
        max_records = len(lines)
        min_records = 0
        print('start')
        input_file.seek(0)
        execc = ExecuteChecker()
        syntaxc = SyntaxChecker()
        for i, line in enumerate(tqdm(input_file, desc='Rewriting', total=max_records)):

            json_obj = json.loads(line)
            if i < max_records and i >= min_records:
                if flag2 in json_obj:
                    continue
                code_to_rewrite = json_obj[flag1]
                lang = json_obj['type']
                # lang = 'cpp'
                
                if todo == 'rewrite':
                    rewritten_code = rewrite_code(code_to_rewrite, lang, tokenizer, model, json_obj)
                else:
                    rewritten_code = retrans_code(code_to_rewrite, lang, tokenizer, model, json_obj)

                if rewritten_code:
                    json_obj[flag2] = rewritten_code
                    json_obj_str = json.dumps(json_obj)
                    output_file.write(json_obj_str + '\n')
                else:
                    print(rewritten_code)

        print('regen done!')



if __name__ == "__main__":
    fire.Fire(main)
