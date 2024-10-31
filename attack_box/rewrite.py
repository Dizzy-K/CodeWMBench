import sys
import os
# os.environ["CUDA_VISIBLE_DEVICES"] = "0"
import fire
import torch
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModelForCausalLM, GenerationConfig
from transformers import LlamaForCausalLM, CodeLlamaTokenizer
import subprocess
import glob
import re
import json

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
    inputs = tokenizer(prompts, return_tensors="pt", max_length=MAX_INPUT_LEN, truncation=True, padding=False)
    real_prompts = tokenizer.batch_decode(inputs["input_ids"])[0]
    input_ids = inputs["input_ids"].to(device)
    #print("prompts len =",len(prompts),"input_ids shape =",input_ids.shape)
    if input_ids.shape[1] == MAX_INPUT_LEN:
        print("[!] input_ids len == MAX_INPUT_LEN")
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

def generate_prompt(text, lang, type='rewrite'):
    PROMPT_TEMPLATES={
        "rewrite": (
            "Below is an instruction that describes a task. "
            "Write a response that appropriately completes the request.\n\n"
            "### Instruction:\n  Here is a {lang} program code. Please rewrite it to enhance its efficiency, readability, and runnability. he revised code should be of the same length (in terms of lines) as the original code. No explanation is needed; only the revised code should be provided. Here's the original code:\n```\n{code}\n```\n\n### Response:"
        ),
        "wizardcoder_comment": (
            "Below is an instruction that describes a task. "
            "Write a response that appropriately completes the request.\n\n"
            "### Instruction:\n The following is a C/C++ function, summarize this function in a short sentence: \n```\n{code}\n```\n\n### Response:"
        ),
    }
    prompt_template = PROMPT_TEMPLATES[type]
    return prompt_template.format(code=text, lang=lang)

def rewrite_code(code, lang, tokenizer, model):
    # 生成重写代码的提示
    prompt = generate_prompt(code, lang, type='rewrite')
    #print(prompt)
    _output, _ = evaluate(prompt, tokenizer, model)
    
    raw_output = _output[0]
    if "### Response:" in raw_output:
        final_output = raw_output.split("### Response:")[1].strip()
    else:
        final_output = raw_output
        print(raw_output)
    
    return final_output

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

def main(
    input_data_path = "/home/dizzylong/work/SrcMarker-main/results/4bit_transformer_seed_1337_csn_java_github_java_funcs_test.jsonl",
    output_file_path = 'data/rewritten_srcmark.jsonl',
    check = 'after_watermark',
    load_8bit: bool = False,
    base_model: str = "/home/dizzylong/work/model/CodeLlama-7b-Instruct-hf",
):
    assert base_model, (
        "Please specify a --base_model, e.g. --base_model='bigcode/starcoder'"
    )

    code_to_rewrite = ''
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

    passed_count = 0
    original_count = 0
    lang = 'cpp'
    params = '0.25,0.25,0.25,0.25'
    codebleu = []
    

    with open(input_data_path, 'r') as input_file, open(output_file_path, 'w') as output_file:
        print(input_data_path)
        lines = input_file.readlines()
        max_records = len(lines)
        min_records = 0
        print('start')
        # time.sleep(60 * 15)
        input_file.seek(0)
        for i, line in enumerate(tqdm(input_file, desc='Rewriting', total=max_records)):
            # print('1')
            json_obj = json.loads(line) 
            if i < max_records and i >= min_records:
                if 'rewritten_code' in json_obj and json_obj[check] != '':
                    continue
                code_to_rewrite = json_obj[check]
                # lang = json_obj['type']
                lang = 'cpp'
                
                rewritten_code = rewrite_code(code_to_rewrite, lang, tokenizer, model)
                # pattern = r"```\n(.*?)```"
                # matches = re.findall(pattern, rewritten_code, re.DOTALL)
                matches = extract_code(rewritten_code)
                # print(rewritten_code,'\n\n', matches)

                try:
                    json_obj['rewritten_code'] = matches[0]
                except:
                    json_obj['rewritten_code'] = rewritten_code
                json_obj_str = json.dumps(json_obj)
                output_file.write(json_obj_str + '\n')
                # else:
                #     print(rewritten_code)

        print('rewrite done!')



if __name__ == "__main__":
    fire.Fire(main)
