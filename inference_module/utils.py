import json
import os


templates_path = 'inference_module/templates'


def get_data(data_path):
    with open(data_path, 'r') as file:
        data = [json.loads(line) for line in file]
    return data

def get_prompt_template(prompt_strategy='base'):
    template_path = os.path.join(templates_path, f"{prompt_strategy}.json")
    print(template_path)
    with open(template_path, 'r') as file:
        template = json.load(file)

    return template



