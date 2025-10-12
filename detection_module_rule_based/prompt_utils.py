import json
import os
import re

nl_descriptions = json.load(open("detection_module_rule_based/NL_descriptions.json"))
code_path = "detection_module_rule_based/detect_results"

categories = list(nl_descriptions.keys())


def reformat_elements(elements):
    for key, value in elements.items():
        if key == 'NAME':
            elements[key] = re.sub(r'^<.*>\.', '', value)
    return elements

def generate_rule_prompt(code_id, categories=categories, case_limit=3):
    """
    Generate a prompt for a given category.
    """
    if code_id.endswith('.cpp'):
        code_id = code_id[:-4]

    result_path = os.path.join(code_path, code_id)

    prompt = ""
    for category in categories:

        # detected entry extract [{type: "METHOD", elements: {NAME: "solve", LINE_NUMBER: "17"}}]
        detected_entries = []
        for file in nl_descriptions[category]['target_files']:
            if os.path.exists(os.path.join(result_path, file)):
                json_data = json.load(open(os.path.join(result_path, file), 'r'))
                for result in json_data['results'][:case_limit]:
                    detected_entries.append(result['elements'])
        
        if len(detected_entries) == 0:
            continue

        summary = nl_descriptions[category]['summary']
        mapping = nl_descriptions[category]['mapping']
        rationale = nl_descriptions[category]['rationale']

        prompt += f"{summary}\n"

        for entry in detected_entries:
            print(entry)
            # entry -> {NAME: "solve", LINE_NUMBER: "17"}
            entry = reformat_elements(entry)
            prompt += f"{mapping.format(**entry)}\n"

        prompt += f"{rationale}\n\n"

    return prompt


if __name__ == "__main__":
    import sys
    
    # set the default code ID or get it from the command line arguments
    if len(sys.argv) > 1:
        test_code_id = sys.argv[1]
    else:
        test_code_id = "s003523064"  # default value, change it to the actual code ID
    
    # option to test specific categories
    if len(sys.argv) > 2:
        test_categories = sys.argv[2].split(',')
    else:
        test_categories = categories
    
    print(f"generating prompt for code ID '{test_code_id}'...")
    result = generate_prompt(test_code_id, test_categories)
    print("\ngenerated prompt:")
    print("-" * 50)
    print(result)
    print("-" * 50)
    print(f"prompt length: {len(result)} characters")


