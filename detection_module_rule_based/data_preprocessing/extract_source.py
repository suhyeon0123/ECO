import json
import os
import sys


def load_data_jsonl(file_path):
    with open(file_path, 'r') as f:
        data = [json.loads(line) for line in f.readlines()]
    return data

def save_code_to_file(code_id, code: str, output_dir):
    file_name = code_id + ".cpp"
    full_path = os.path.join(output_dir, file_name)

    # Check if the file already exists
    if not os.path.isfile(full_path):
        with open(full_path, 'w') as f:
            f.write(code)


def extract_sources(jsonl_file, output_dir, extract_elements=['src']):

    data = load_data_jsonl(jsonl_file)
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    for _, entry in enumerate(data):
        for extract_element in extract_elements:
            id_key = f"{extract_element}_id"
            content_key = f"{extract_element}_code"
            code_id, code_snippet = entry[id_key], entry[content_key]
            save_code_to_file(code_id, code_snippet, output_dir)



if __name__ == "__main__":
    jsonl_file = sys.argv[1]
    output_dir = sys.argv[2]
    extract_sources(jsonl_file, output_dir, ['src'])
