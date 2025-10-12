import os
import json
import pandas as pd
import glob
import re
import sys


class CodeExtractor:
    """Class for extracting code blocks from text"""
    
    @staticmethod
    def extract_code_from_markdown(text):
        """
        1) Find the first code block that starts with '```' (including language) and ends with '```'
        2) Return the content if found, None otherwise
        """
        pattern = r"```(?:cpp|c|python|java|\w*)\s*(.*?)```"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()  # Text inside the code block
        return None

    @staticmethod
    def extract_c_style_main_function(text):
        """
        Extract just the 'main' function block from the given text
        """
        main_start = re.search(r"\b(?:int\s+)?main\s*\(", text)
        if not main_start:
            return text  # Return original if not found

        open_braces = 0
        closing_brace_position = -1
        main_function_started = False

        char_pos = main_start.end()
        while char_pos < len(text):
            if text[char_pos] == "{":
                open_braces += 1
                if not main_function_started:
                    main_function_started = True
            elif text[char_pos] == "}":
                open_braces -= 1
                if open_braces == 0 and main_function_started:
                    closing_brace_position = char_pos
                    break
            char_pos += 1

        if closing_brace_position != -1:
            return text[: closing_brace_position + 1]
        else:
            return text

    @staticmethod
    def extract_code_or_main_function(text):
        """
        (1) First, extract the first code block wrapped in ```cpp ... ``` from the LLM response
        (2) If code block exists, return it entirely (recommended) or extract just the main function
        """
        code_block = CodeExtractor.extract_code_from_markdown(text)
        if code_block is None:
            # fallback: search for main using existing logic
            return CodeExtractor.extract_c_style_main_function(text)
        else:
            # Return the entire code block (recommended)
            return code_block


class ResultProcessor:
    """Class for processing and formatting inference results"""
    
    @staticmethod
    def process_and_save_results(reference_file_path, input_dir, output_file):
        # Find all prompt_*.json* files
        result_json_files = []
        result_json_files += glob.glob(os.path.join(input_dir, "s[0-9]*.json*"))
        result_json_files += glob.glob(os.path.join(input_dir, "cf_[0-9]*_[0-9]*.json*"))

        # Load reference data file
        reference_df = pd.read_json(reference_file_path, lines=True, orient="records")

        # Process each file and collect results
        results_data = ResultProcessor._extract_results_from_json_files(result_json_files)

        # Create final dataframe with results
        merged_df = ResultProcessor._merge_results_with_reference_data(reference_df, results_data)
        
        # Save to JSONL file (only rows with generated answers)
        ResultProcessor._save_results_to_jsonl(merged_df, output_file)
        
        print(f"Conversion complete: {len(results_data)} files saved to {output_file}")
        return len(results_data)
    
    @staticmethod
    def _extract_results_from_json_files(json_files):
        results_data = []
        for file_path in json_files:
            print(f"Processing file: {file_path}")
            # Extract data from JSON file
            if file_path.endswith('.json'):
                with open(file_path, 'r') as f:
                    json_contents = [json.load(f)]
            elif file_path.endswith('.jsonl'):
                with open(file_path, 'r') as f:
                    json_contents = [json.loads(line) for line in f]
            
            # Extract src_id from filename
            file_name = os.path.basename(file_path)
            src_id = file_name.split('.')[0]
            
            generated_answers = []
            for json_record in json_contents:
                # Extract and process generated code
                try:
                    generated_code = json_record["response"]
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
                    generated_code = "int main() { return 0; }"

                processed_code = CodeExtractor.extract_code_or_main_function(generated_code)
                generated_answers.append(processed_code)
            
            # Add to results data
            results_data.append({
                "src_id": src_id,
                "generated_answers": generated_answers  
            })
            
        return results_data
    
    @staticmethod
    def _merge_results_with_reference_data(test_df, results_data):
        # Create a copy of test_df with all columns preserved
        merged_df = test_df.copy()
        # Initialize with empty lists
        merged_df["generated_answers"] = merged_df.apply(lambda x: [], axis=1)
        
        # Convert results_data to DataFrame for easy merging
        results_df = pd.DataFrame(results_data)
        
        # Update generated_answers where src_id matches
        missing_src_ids = []
        for _, row in results_df.iterrows():
            matching_indices = merged_df[merged_df["src_id"] == row["src_id"]].index
            if len(matching_indices) > 0:
                merged_df.at[matching_indices[0], "generated_answers"] = row["generated_answers"]
        
        # Find missing src_ids
        for _, row in merged_df.iterrows():
            if len(row["generated_answers"]) == 0:
                missing_src_ids.append(row["src_id"])
        
        # Output missing src_ids
        if missing_src_ids:
            print(f"No generated answers for the following src_ids: {missing_src_ids}")
            
        return merged_df
    
    @staticmethod
    def _save_results_to_jsonl(merged_df, output_file):
        with open(output_file, 'w', encoding='utf-8') as f:
            for _, row in merged_df.iterrows():
                if len(row["generated_answers"]) > 0:
                    f.write(json.dumps(row.to_dict(), ensure_ascii=False) + '\n')


if __name__ == "__main__":
    # Command examples:
    # python3 inference_module/output_format.py   \
    # BRIDGE_data/PIE_test.jsonl \
    # results/inference_results/rules/qwen2.5-coder_7b_k_sample \
    # results/inference_results/rules/qwen2.5-coder_7b_k_sample/sampled_results.jsonl

    # python3 inference_module/output_format.py   \
    # BRIDGE_data/PIE_test.jsonl \
    # results/inference_results/BRIDGE_o4 \
    # results/inference_results/BRIDGE_o4/sampled_results.jsonl

    # python3 inference_module/output_format.py   \
    # BRIDGE_data/codeforce_test.jsonl \
    # results/inference_results/codeforce/base/gpt-4o \
    # results/inference_results/codeforce/base/gpt-4o/sampled_results.jsonl

    if len(sys.argv) != 4:
        print("Usage: python output_format.py <reference_file_path> <input_dir> <output_file>")
        sys.exit(1)
        
    reference_file_path = sys.argv[1]
    input_dir = sys.argv[2]
    output_file = sys.argv[3]
    
    ResultProcessor.process_and_save_results(reference_file_path, input_dir, output_file)