import sys
import time
from ollama import Client
import json
import os
import argparse
from datetime import datetime

# analysis_prompt = """Identify optimization points in this slow code and explain how the transformation to the fast code improves runtime. Provide the output in the following JSON format:

# {{
#     "optimization_points": [
#         {
#             "description": "Describe the detail inefficiency issue in slow_code and explain the specific improvement in fast_code.",
#             "runtime_improvement": "An integer rating (1-10) of how much this optimization improves runtime.",
#             "category": "Algorithm | Data Structure | Memory Management | Code Execution | System Interaction | ETC"
#         },
#         ...
#     ]
# }}

# Slow Code:
# {slow_code}

# Fast Code:
# {fast_code}
# 
# ### Analysis:
# """

def get_data(data_path):
    with open(data_path, 'r') as file:
        data = [json.loads(line) for line in file]
    return data


def call_LLM(client, model, prompt, temperature):
    return client.chat(
        model=model,
        messages=[{
            'role': 'user',
            'content': prompt,
        }],
        options = {
            "temperature": temperature
        }
    )

def load_template(templates_path, template_name):
    template_path = os.path.join(templates_path, template_name)
    with open(template_path, 'r') as file:
        return json.load(file)['prompt_no_input']

def analyze_code(client, model, data, template, output_dir, temperature=0.0):
    for idx, item in enumerate(data):
        code_id = item['src_id']
        
        # check if the analysis result file already exists
        output_file = os.path.join(output_dir, f"analysis_{idx+1}.json")
        if os.path.exists(output_file):
            print(f"file {output_file} already exists. skipping.")
            continue
            
        args = {'slow_code': item['src_code'], 'fast_code': item['tgt_code']}
        prompt = template.format(**args)

        start_time = time.time()  
        response = call_LLM(client, model, prompt, temperature)
        elapsed_time = time.time() - start_time

        # construct the result as a dictionary
        result = {
            "prompt": prompt,
            "response": response.message.content,
            "elapsed_time": elapsed_time,
            "model": model
        }
        
        # save the result as a separate JSON file for each prompt
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
        
        print(f"{response.message.content}")
        print(f"Time taken: {elapsed_time} seconds")

def main():
    parser = argparse.ArgumentParser(description='code analysis execution tool')
    parser.add_argument('--model', default='deepseek-r1:32b', help='name of the LLM model to use')
    parser.add_argument('--input_file_path', default='BRIDGE_data/HQ_data.jsonl', help='path to the data file to analyze')
    parser.add_argument('--templates_path', default='detection_module_LLM_based/templates', help='path to the template directory')
    parser.add_argument('--template_name', default='code_analysis.json', help='name of the template file to use')
    parser.add_argument('--output_dir', default='BRIDGE_data/distilled_rationales', help='directory to save the results')
    parser.add_argument('--temperature', type=float, default=0.0, help='LLM temperature')
    parser.add_argument('--host', default='http://localhost:11434', help='Ollama server address')
    
    args = parser.parse_args()
    
    # create the directory to save the results
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    # initialize the Ollama client
    client = Client(host=args.host)
    
    # load the template
    template = load_template(args.templates_path, args.template_name)
    
    # load the data
    data = get_data(args.file_path)
    
    # run the code analysis
    analyze_code(client, args.model, data, template, args.output_dir, args.temperature)

if __name__ == "__main__":
    main()
