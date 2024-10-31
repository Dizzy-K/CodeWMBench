import os
import json
import random
import re
from bs4 import BeautifulSoup
import lib2to3.refactor
from tqdm import tqdm

# def extract_input_output(file_path):
#     try:
#         with open(file_path, "r", encoding="utf-8") as file:
#             content = file.read()
#         soup = BeautifulSoup(content, 'html.parser')
        
#         samples = []
#         i = 1
#         found_samples = False

#         # 先尝试使用"Sample Input X"和"Output for the Sample Input X"格式
#         while True:
#             input_tag = soup.find('h2', string=f'Sample Input {i}')
#             output_tag = soup.find('h2', string=f'Output for the Sample Input {i}')

#             if not input_tag or not output_tag:
#                 if i == 1:  # 如果第一次就没有找到，尝试另一种格式
#                     input_tag = soup.find('h2', string='Sample Input')
#                     output_tag = soup.find('h2', string='Output for the Sample Input')
#                 break

#             found_samples = True
#             input_example = input_tag.find_next('pre').text.strip() if input_tag.find_next('pre') else ""
#             output_example = output_tag.find_next('pre').text.strip() if output_tag.find_next('pre') else ""

#             samples.append((input_example, output_example))
#             i += 1

#         # 如果第一种格式没有找到，尝试第二种格式
#         if not found_samples and input_tag and output_tag:
#             input_example = input_tag.find_next('pre').text.strip() if input_tag.find_next('pre') else ""
#             output_example = output_tag.find_next('pre').text.strip() if output_tag.find_next('pre') else ""

#             samples.append((input_example, output_example))

#         formatted_samples = '&&&'.join([f'{inp}***{out}' for inp, out in samples])
#         return formatted_samples
#     except Exception as e:
#         print(f"An error occurred while processing {file_path}: {e}")
#         return None

def extract_specific_tags(soup):
    # 定义要匹配的模式
    patterns = [
        r"Sample Input\s*\d*", r"Output for the Sample Input\s*\d*",
        r"Sample Output\s*\d*", r"入力例\s*\d*", r"出力例\s*\d*", r"サンプル入力\s*\d*", r"Sample input\s*\d*"
    ]
    extracted_data = []
    temp_data = {}

    for pattern in patterns:
        for tag in soup.find_all(['h1', 'h2', 'h3'], string=re.compile(pattern)):
            next_tag = tag.find_next_sibling("pre")
            if next_tag:
                temp_data[tag.text.strip()] = next_tag.text.strip()

    # 将匹配到的输入和输出配对
    inputs = [v for k, v in temp_data.items() if 'Input' in k or '入力例' in k]
    outputs = [v for k, v in temp_data.items() if 'Output' in k or '出力例' in k]

    for i, o in zip(inputs, outputs):
        extracted_data.append([i, o])

    return extracted_data

def extract_input_output(full_path):
    extracted_contents = []

    with open(full_path, 'r', encoding='utf-8') as file:
        content = file.read()

    soup = BeautifulSoup(content, 'lxml')
    extracted_contents.extend(extract_specific_tags(soup))

    return extracted_contents




def process_cn_files(input_file_directory, test_file_directory, num_files, output_file, langs):
    filetails = {'C++' : '.cpp', 'Python' : '.py', 'C': '.c', 'JavaScript': '.js', 'Java': '.java'}
    with open(output_file, 'a', encoding='utf-8') as out_file:
        if num_files == -1:
            num_files = len(os.listdir(input_file_directory))
        for i in tqdm(range(1, num_files + 1)):
            for lang in langs:
                folder_name = f"p{str(i).zfill(5)}"
                folder = os.path.join(input_file_directory, folder_name, lang)
                filename = f"p{str(i).zfill(5)}.html"
                full_path = os.path.join(test_file_directory, filename)

                if os.path.exists(folder) and os.path.exists(full_path):
                    filetail = filetails[lang]
                    lang_files = [f for f in os.listdir(folder) if f.endswith(filetail)]
                    selected_files = random.sample(lang_files, min(50, len(lang_files)))
                    samples = extract_input_output(full_path)
                    if not samples:
                        continue
                    for file_name in selected_files:
                        file_path = os.path.join(folder, file_name)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as file:
                                code = file.read()
                                json_line = json.dumps({"filename": folder_name, "code": code, "test_case": samples, "type": lang})
                                out_file.write(json_line + '\n')
                        except Exception as e:
                            # print(f"An error occurred while processing {file_path}: {e}")
                            pass
                # else:
                #     print(f"Folder not found: {folder}")

def process_csn_files(file_path, output_file, num_samples=1000):
    file_name = os.path.basename(file_path)
    match = re.search(r'(java|python)_(train|test|valid)_[0-9]+\.jsonl', file_name)
    if not match:
        raise ValueError("File name does not match the expected pattern.")

    language_type = match.group(1).capitalize()  # 获取并大写首字母，如 Java 或 Python

    with open(file_path, 'r', encoding='utf-8') as file:
        data = [json.loads(line) for line in file]

    selected_data = data
    # selected_data = random.sample(data, min(num_samples, len(data)))

    new_data = []
    # for entry in tqdm(selected_data):
    #     new_entry = {
    #         "code": entry["code"],
    #         "type": language_type
    #     }
    #     new_data.append(new_entry)

    for entry in tqdm(selected_data):
        new_entry = entry
        new_entry['type'] = language_type
        new_data.append(new_entry)

    with open(output_file, 'a', encoding='utf-8') as file:
        for entry in data:
            file.write(json.dumps(entry) + "\n")




def main():
    # input_cn_directory = "/home/dizzylong/work/lab/data/Codenet/Project_CodeNet/data"
    # test_cn_directory = "/home/dizzylong/work/lab/data/Codenet/Project_CodeNet/problem_descriptions"
    output_jsonl_file = "/home/dizzylong/work/CoProtector/clean_CSN.jsonl"

    # lang = ['C++', 'Python']
    # process_cn_files(input_cn_directory, test_cn_directory, -1, output_jsonl_file, lang)
    # print("CodeNet data done")

    input_csn_directory = "/home/dizzylong/work/lab/data/java/final/jsonl/train/java_train_0.jsonl"
    process_csn_files(input_csn_directory, output_jsonl_file)
    # input_csn_directory = "/home/dizzylong/work/lab/data/python/final/jsonl/train/python_train_0.jsonl"
    # process_csn_files(input_csn_directory, output_jsonl_file)
    print("CodeSearchNet data done")



if __name__ == '__main__':
    main()
    # t = 0
    # for i in tqdm(range(0, 4052)):
    #     if os.path.exists(f'/home/dizzylong/work/lab/data/Codenet/Project_CodeNet/problem_descriptions/p{str(i).zfill(5)}.html'):
    #         a = read_and_extract_html_content(f'/home/dizzylong/work/lab/data/Codenet/Project_CodeNet/problem_descriptions/p{str(i).zfill(5)}.html')
    #         if not a:
    #             t += 1
    # print(t)
        # print(i, extract_input_output(f'/home/dizzylong/work/lab/data/Codenet/Project_CodeNet/problem_descriptions/p{str(i).zfill(5)}.html'))
